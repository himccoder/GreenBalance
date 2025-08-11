.PHONY: build up down logs restart clean

SHELL := /bin/bash
COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

build:
	$(COMPOSE) build

up:
	@if [ ! -f .env ]; then cp env_example.txt .env; fi
	$(COMPOSE) up -d
	@echo "\nAccess:"
	@echo "- http://localhost:5000 (Weight Manager)"
	@echo "- http://localhost:5001 (Weight Viewer)"
	@echo "- http://localhost:8404/stats (HAProxy Stats)"
	@echo "- http://localhost:80 (LB)"
	@echo "- http://localhost:5000/historical-simulation (Historical Sim)"

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

restart: down up

clean:
	$(COMPOSE) down -v --remove-orphans
	docker rmi $$(docker images -q -f label=greencdn 2>/dev/null) || true

