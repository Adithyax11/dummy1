import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import clients
from .config import settings

app = FastAPI(title="api-gateway")


class OrderRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # Reuse the caller's ID if provided, otherwise make one
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.get("/products")
async def products(request: Request):
    status, body = await clients.forward(
        "inventory", "GET", f"{settings.inventory_url}/products",
        request.state.request_id,
    )
    return JSONResponse(status_code=status, content=body)


@app.post("/orders")
async def create_order(req: OrderRequest, request: Request):
    status, body = await clients.forward(
        "order", "POST", f"{settings.order_url}/orders",
        request.state.request_id, json=req.model_dump(),
    )
    return JSONResponse(status_code=status, content=body)


@app.get("/orders/{order_id}")
async def get_order(order_id: int, request: Request):
    status, body = await clients.forward(
        "order", "GET", f"{settings.order_url}/orders/{order_id}",
        request.state.request_id,
    )
    return JSONResponse(status_code=status, content=body)