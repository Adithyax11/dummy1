# dummy1

A small Python microservices stack used as a test target for an OpenTelemetry project.
The services are deliberately **uninstrumented**. They exist to produce realistic traffic:
HTTP hops, DB calls, async messaging, errors, and latency.

## Architecture

```
browser -> frontend (nginx) -> api-gateway -> order-service -> inventory-service -> Postgres
                                          \                \-> payment-service
                                           \-> inventory      \-> RabbitMQ -> notification-worker
```

| Service | Tech | Role |
|---|---|---|
| frontend | nginx + vanilla JS | UI, proxies `/api/*` to the gateway |
| api-gateway | FastAPI | Entry point, stamps `X-Request-ID` |
| order-service | FastAPI, SQLAlchemy | Orchestrates reserve -> charge -> save -> publish |
| inventory-service | FastAPI, SQLAlchemy | Stock in Postgres |
| payment-service | FastAPI | Fake payments with configurable latency and failure rate |
| notification-worker | pika | Consumes `order.created` from RabbitMQ |
| postgres, rabbitmq | | Infra |

## Quick start

    cp .env.example .env        # Windows CMD: copy .env.example .env
    docker compose up --build -d
    docker compose ps           # wait for everything to be healthy

Open http://localhost:8080 (or your `FRONTEND_PORT`).

## Ports (host)

| Port | What | Bound to |
|---|---|---|
| 8080 (`FRONTEND_PORT`) | Web UI | all interfaces |
| 8000 (`GATEWAY_PORT`) | API gateway | localhost |
| 5432 (`POSTGRES_PORT`) | Postgres | localhost |
| 5672 / 15672 | RabbitMQ / management UI (guest/guest) | localhost |
| 8089 | Locust UI (only with the `load` profile) | localhost |

Inventory (8001), payment (8002), and order (8003) are reachable only inside the compose network.

## API (through the gateway)

| Endpoint | Behavior |
|---|---|
| `GET /health` | Liveness |
| `GET /products` | List products and stock |
| `POST /orders` `{"sku","quantity"}` | 201 confirmed, 404 unknown sku, 409 out of stock, 402 payment declined, 503/504 downstream down or slow |
| `GET /orders/{id}` | 200 or 404 |
| `GET /slow?min_ms=&max_ms=` | Sleeps a random time (max 8000 ms) in order-service |
| `GET /error?code=500` | 500 raises a real exception in order-service; 400-599 returns a clean HTTP error |
| `GET /chain?depth=N` | Bounces gateway <-> order-service N times (max 20) and returns the path |

Every response carries `X-Request-ID`. A caller-supplied ID is reused and passed on through each hop.

Every service also has `GET /health`. The worker has no HTTP interface.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `POSTGRES_USER` / `_PASSWORD` / `_DB` / `_PORT` | testbed / testbed / testbed / 5432 | Database |
| `RABBITMQ_USER` / `_PASSWORD` / `_PORT` / `_MGMT_PORT` | guest / guest / 5672 / 15672 | Broker |
| `FRONTEND_PORT` | 8080 | Host port for the UI |
| `GATEWAY_PORT` | 8000 | Host port for the gateway |
| `FAILURE_RATE` | 0.10 | Share of charges declined (402) |
| `MIN_LATENCY_MS` / `MAX_LATENCY_MS` | 50 / 500 | Random delay per charge |

## Testing

    python scripts/smoke_test.py          # hits every endpoint once (needs the stack running)
    bash scripts/trigger_errors.sh        # forces errors, slow paths, a deep chain, 20 orders

    docker compose --profile load up --build -d loadgen   # Locust UI at http://localhost:8089
    docker compose --profile load stop loadgen

    # Unit tests (venv with requirements-dev.txt installed)
    cd services/payment-service && python -m pytest
    cd services/inventory-service && python -m pytest

Load tests drain stock. Refill it with:

    docker compose exec postgres psql -U testbed -d testbed -c "UPDATE products SET stock = 1000;"

## Everyday commands

    docker compose up --build -d order-service   # rebuild one service after a code change
    docker compose logs -f notification-worker
    docker compose down                          # stop, keep data
    docker compose down -v                       # stop and wipe the database

## Failure experiments

    docker compose stop payment-service    # orders -> 503, stock is released
    docker compose stop rabbitmq           # orders still succeed, notifications are lost
    docker compose stop inventory-service  # orders and /products -> 503

## Using it as an OTel target

Nothing here is instrumented. Attach your OTel setup to the containers or the compose file.
`X-Request-ID` gives you a simple correlation ID to compare against trace IDs.

## Layout

    services/   api-gateway, order-service, inventory-service, payment-service, notification-worker
    frontend/   static UI + nginx config
    db/         init.sql (schema and seed data)
    loadgen/    Locust file
    scripts/    smoke and error scripts