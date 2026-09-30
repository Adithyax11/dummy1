import os
import time
import requests

BASE = os.getenv("BASE", "http://127.0.0.1:8000")


def hit(label, method, path, json_body=None):
    url = BASE + path

    start = time.perf_counter()

    try:
        response = requests.request(
            method,
            url,
            json=json_body,
            timeout=30
        )

        elapsed = time.perf_counter() - start

        print(f"{label:<28} {response.status_code}  {elapsed:.3f}s")

    except requests.RequestException as e:
        elapsed = time.perf_counter() - start
        print(f"{label:<28} ERROR  {elapsed:.3f}s  {e}")


print("--- errors ---")

hit("500 unhandled exception", "GET", "/error")

hit("503 simulated", "GET", "/error?code=503")

hit("404 simulated", "GET", "/error?code=404")

hit(
    "unknown sku",
    "POST",
    "/orders",
    {"sku": "NOPE", "quantity": 1}
)

hit(
    "out of stock",
    "POST",
    "/orders",
    {"sku": "CHOC-001", "quantity": 100}
)


print()
print("--- slow ---")

hit("slow 1-3s", "GET", "/slow?min_ms=1000&max_ms=3000")

hit("slow 4-6s", "GET", "/slow?min_ms=4000&max_ms=6000")


print()
print("--- deep chain ---")

hit("chain depth 20", "GET", "/chain?depth=20")


print()
print("--- 20 orders (watch for 402 payment declines) ---")

for i in range(1, 21):
    hit(
        f"order {i}",
        "POST",
        "/orders",
        {"sku": "APPLE-001", "quantity": 1}
    )