import random

from locust import HttpUser, between, task

SKUS = ["APPLE-001", "BREAD-001", "MILK-001", "COFFEE-001"]


class Shopper(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        self.order_ids = []

    @task(5)
    def browse(self):
        self.client.get("/products")

    @task(4)
    def place_order(self):
        body = {"sku": random.choice(SKUS), "quantity": random.randint(1, 3)}
        with self.client.post("/orders", json=body, catch_response=True,
                              name="/orders [POST]") as r:
            if r.status_code == 201:
                self.order_ids.append(r.json()["id"])
                r.success()
            elif r.status_code in (402, 409):
                r.success()  # expected: payment declined / out of stock
            else:
                r.failure(f"unexpected {r.status_code}")

    @task(2)
    def lookup_order(self):
        if self.order_ids:
            oid = random.choice(self.order_ids)
            self.client.get(f"/orders/{oid}", name="/orders/[id]")

    @task(1)
    def slow(self):
        self.client.get("/slow?min_ms=200&max_ms=1500")

    @task(1)
    def error(self):
        with self.client.get("/error", catch_response=True) as r:
            if r.status_code == 500:
                r.success()  # this endpoint is supposed to fail
            else:
                r.failure(f"expected 500, got {r.status_code}")

    @task(1)
    def chain(self):
        self.client.get(f"/chain?depth={random.randint(2, 8)}", name="/chain")