import asyncio
import random
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings

app = FastAPI(title="payment-service")


class ChargeRequest(BaseModel):
    order_id: int | None = None
    amount_cents: int = Field(gt=0)


@app.get("/health")
def health():
    return {"status": "ok", "service": "payment-service"}


@app.post("/charge")
async def charge(req: ChargeRequest):
    latency_ms = random.randint(settings.min_latency_ms, settings.max_latency_ms)
    await asyncio.sleep(latency_ms / 1000)

    if random.random() < settings.failure_rate:
        raise HTTPException(status_code=402, detail="payment declined")

    return {
        "payment_id": str(uuid.uuid4()),
        "status": "approved",
        "amount_cents": req.amount_cents,
        "latency_ms": latency_ms,
    }