from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from .db import get_db
from .models import Product

app = FastAPI(title="inventory-service")


class ReserveRequest(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


def product_to_dict(p: Product) -> dict:
    return {
        "sku": p.sku,
        "name": p.name,
        "price_cents": p.price_cents,
        "stock": p.stock,
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "inventory-service"}


@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    rows = db.scalars(select(Product).order_by(Product.sku)).all()
    return [product_to_dict(p) for p in rows]


@app.get("/stock/{sku}")
def get_stock(sku: str, db: Session = Depends(get_db)):
    product = db.get(Product, sku)
    if product is None:
        raise HTTPException(status_code=404, detail="unknown sku")
    return product_to_dict(product)


@app.post("/reserve")
def reserve(req: ReserveRequest, db: Session = Depends(get_db)):
    # Atomic decrement: only succeeds if enough stock is left
    result = db.execute(
        update(Product)
        .where(Product.sku == req.sku, Product.stock >= req.quantity)
        .values(stock=Product.stock - req.quantity)
    )

    if result.rowcount == 0:
        db.rollback()
        if db.get(Product, req.sku) is None:
            raise HTTPException(status_code=404, detail="unknown sku")
        raise HTTPException(status_code=409, detail="insufficient stock")

    db.commit()
    product = db.get(Product, req.sku)
    return {
        "sku": product.sku,
        "reserved": req.quantity,
        "remaining": product.stock,
        "unit_price_cents": product.price_cents,
        "total_cents": product.price_cents * req.quantity,
    }

@app.post("/release")
def release(req: ReserveRequest, db: Session = Depends(get_db)):
    # Undo a reservation (used when payment fails after stock was reserved)
    result = db.execute(
        update(Product)
        .where(Product.sku == req.sku)
        .values(stock=Product.stock + req.quantity)
    )

    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="unknown sku")

    db.commit()
    product = db.get(Product, req.sku)
    return {"sku": product.sku, "released": req.quantity, "stock": product.stock}