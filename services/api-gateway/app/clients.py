import httpx
from fastapi import HTTPException

from .config import settings

_client = httpx.AsyncClient(timeout=settings.http_timeout_s)


async def forward(service: str, method: str, url: str,
                  request_id: str, json: dict | None = None) -> tuple[int, dict | list]:
    """Call a downstream service and return (status_code, body) as-is."""
    try:
        resp = await _client.request(
            method, url, json=json, headers={"X-Request-ID": request_id}
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"{service} timed out")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail=f"{service} unreachable")

    try:
        body = resp.json()
    except ValueError:
        body = {"detail": resp.text}

    return resp.status_code, body