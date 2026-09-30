.PHONY: up down logs smoke errors load load-headless restock reset

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

smoke:
	bash scripts/smoke_test.sh

errors:
	bash scripts/trigger_errors.sh

# Locust web UI at http://localhost:8089
load:
	docker compose --profile load up --build -d loadgen

# 10 users for 1 minute, prints a summary, no UI
load-headless:
	docker compose run --rm loadgen locust -f locustfile.py --headless -u 10 -r 2 -t 1m

# Load tests drain stock, so refill it
restock:
	docker compose exec postgres psql -U testbed -d testbed -c "UPDATE products SET stock = 1000;"

# Wipe everything and start fresh
reset:
	docker compose down -v
	docker compose up --build -d