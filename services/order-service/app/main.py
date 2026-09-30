import logging
import random
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import clients, publisher
from .clients import UpstreamError
from .db import Order, get_db

logger = logging.getLogger("order-service")
app = FastAPI(title="order-service")


class OrderRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


def order_to_dict(o: Order) -> dict:
    return {
        "id": o.id,
        "sku": o.sku,
        "quantity": o.quantity,
        "total_cents": o.total_cents,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def to_http_error(err: UpstreamError) -> HTTPException:
    # Pass meaningful codes through; anything unexpected becomes a 502
    passthrough = {402, 404, 409, 503, 504}
    status = err.status_code if err.status_code in passthrough else 502
    return HTTPException(status_code=status, detail=f"{err.service}: {err.detail}")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "order-service"}


@app.post("/orders", status_code=201)
def create_order(req: OrderRequest, db: Session = Depends(get_db)):
    # 1. Reserve stock (404 unknown sku, 409 out of stock)
    try:
        reservation = clients.reserve_stock(req.sku, req.quantity)
    except UpstreamError as err:
        raise to_http_error(err)

    total_cents = reservation["total_cents"]

    # 2. Charge payment. If it fails, put the stock back.
    try:
        payment = clients.charge(total_cents)
    except UpstreamError as err:
        try:
            clients.release_stock(req.sku, req.quantity)
        except UpstreamError as release_err:
            logger.error("failed to release stock for %s x%d: %s",
                         req.sku, req.quantity, release_err)
        raise to_http_error(err)

    # 3. Save the order
    order = Order(sku=req.sku, quantity=req.quantity,
                  total_cents=total_cents, status="confirmed")
    db.add(order)
    db.commit()
    db.refresh(order)

    response = {**order_to_dict(order), "payment_id": payment["payment_id"]}

    # 4. Tell the rest of the system (best effort, never fails the order)
    publisher.publish_order_created(response)

    return response


@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return order_to_dict(order)


# ---------- test-behavior endpoints ----------

@app.get("/slow")
def slow(min_ms: int = Query(500, ge=0, le=8000),
         max_ms: int = Query(3000, ge=0, le=8000)):
    lo, hi = sorted((min_ms, max_ms))
    delay = random.randint(lo, hi)
    time.sleep(delay / 1000)
    return {"service": "order-service", "slept_ms": delay}


@app.get("/error")
def error(code: int = Query(500, ge=400, le=599)):
    if code == 500:
        # Unhandled on purpose: gives a real traceback / exception event
        raise RuntimeError("simulated failure in order-service")
    raise HTTPException(status_code=code, detail=f"simulated {code} from order-service")


@app.get("/chain")
def chain(depth: int = Query(3, ge=1, le=20),
          x_request_id: str | None = Header(None)):
    if depth <= 1:
        return {"path": ["order-service"]}
    try:
        child = clients.chain(depth - 1, x_request_id)
    except UpstreamError as err:
        raise to_http_error(err)
    return {"path": ["order-service", *child["path"]]}