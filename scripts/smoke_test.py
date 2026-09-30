import os
import sys

import httpx

BASE = os.environ.get("BASE", "http://127.0.0.1:8000")
client = httpx.Client(base_url=BASE, timeout=15)
passed = failed = 0


def check(name, expected, actual):
    global passed, failed
    if expected == actual:
        print(f"PASS  {name} ({actual})")
        passed += 1
    else:
        print(f"FAIL  {name} (expected {expected}, got {actual})")
        failed += 1


def order(sku, qty):
    return client.post("/orders", json={"sku": sku, "quantity": qty})


check("GET /health", 200, client.get("/health").status_code)
check("GET /products", 200, client.get("/products").status_code)
check("GET /slow (fast range)", 200, client.get("/slow", params={"min_ms": 50, "max_ms": 100}).status_code)
check("GET /error", 500, client.get("/error").status_code)
check("GET /error?code=503", 503, client.get("/error", params={"code": 503}).status_code)
check("GET /chain?depth=5", 200, client.get("/chain", params={"depth": 5}).status_code)
check("POST /orders unknown sku", 404, order("NOPE", 1).status_code)
check("POST /orders out of stock", 409, order("APPLE-001", 99999).status_code)
check("GET /orders/999999 (missing)", 404, client.get("/orders/999999").status_code)

# Real order: retry a few times because payment declines ~10% of the time
resp = None
for _ in range(5):
    resp = order("APPLE-001", 1)
    if resp.status_code == 201:
        break

check("POST /orders (real order)", 201, resp.status_code)
if resp.status_code == 201:
    oid = resp.json()["id"]
    check(f"GET /orders/{oid}", 200, client.get(f"/orders/{oid}").status_code)

print(f"\npassed: {passed}  failed: {failed}")
sys.exit(1 if failed else 0)