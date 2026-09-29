import httpx

from .config import settings


class UpstreamError(Exception):
    """A downstream service failed or was unreachable."""

    def __init__(self, service: str, status_code: int, detail: str):
        self.service = service
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{service} returned {status_code}: {detail}")


_client = httpx.Client(timeout=settings.http_timeout_s)


def _call(service: str, url: str, payload: dict) -> dict:
    try:
        resp = _client.post(url, json=payload)
    except httpx.TimeoutException as exc:
        raise UpstreamError(service, 504, f"{service} timed out") from exc
    except httpx.RequestError as exc:
        raise UpstreamError(service, 503, f"{service} unreachable") from exc

    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise UpstreamError(service, resp.status_code, str(detail))

    return resp.json()


def reserve_stock(sku: str, quantity: int) -> dict:
    return _call("inventory", f"{settings.inventory_url}/reserve",
                 {"sku": sku, "quantity": quantity})


def release_stock(sku: str, quantity: int) -> dict:
    return _call("inventory", f"{settings.inventory_url}/release",
                 {"sku": sku, "quantity": quantity})


def charge(amount_cents: int) -> dict:
    return _call("payment", f"{settings.payment_url}/charge",
                 {"amount_cents": amount_cents})