# DHT Makefile for Docker operations
.PHONY: help build test lint shell clean docker-build docker-test docker-lint docker-shell docker-clean

# Default target
help:
	@echo "DHT Docker Operations"
	@echo "===================="
	@echo ""
	@echo "Local operations:"
	@echo "  make build       - Build the project locally"
	@echo "  make test        - Run tests locally"
	@echo "  make lint        - Run linting locally"
	@echo "  make clean       - Clean local build artifacts"
	@echo ""
	@echo "Docker operations:"
	@echo "  make docker-build     - Build all Docker images"
	@echo "  make docker-test      - Run tests in Docker"
	@echo "  make docker-lint      - Run linting in Docker"
	@echo "  make docker-shell     - Start interactive shell in Docker"
	@echo "  make docker-workflow  - Run GitHub workflows locally with act"
	@echo "  make docker-clean     - Clean Docker images and containers"
	@echo ""
	@echo "Docker Compose operations:"
	@echo "  make compose-up       - Start all services"
	@echo "  make compose-down     - Stop all services"
	@echo "  make compose-test     - Run test service"
	@echo "  make compose-dev      - Start development environment"

# Local operations
build:
	uv sync --frozen
	uv build

test:
	uv run pytest -v --tb=short

lint:
	uv run ruff check .
	uv run mypy src/

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker operations using DHT commands
docker-build:
	./dhtl.py docker build --target runtime
	./dhtl.py docker build --target test-runner
	./dhtl.py docker build --target development

docker-test:
	./dhtl.py docker test

docker-lint:
	./dhtl.py docker lint

docker-shell:
	./dhtl.py docker shell

docker-workflow:
	./dhtl.py docker workflow push

# Docker Compose operations
compose-up:
	docker compose up -d

compose-down:
	docker compose down

compose-test:
	docker compose run --rm dht-test

compose-dev:
	docker compose run --rm dht-dev

compose-lint:
	docker compose run --rm dht-lint

compose-format:
	docker compose run --rm dht-format

# Clean Docker artifacts
docker-clean:
	docker compose down -v
	docker rmi dht:runtime dht:test dht:dev || true
	docker volume rm dht-cache dht-test-results || true

# Advanced targets
docker-build-nocache:
	docker build --no-cache -f Dockerfile --target runtime -t dht:runtime .
	docker build --no-cache -f Dockerfile --target test-runner -t dht:test .
	docker build --no-cache -f Dockerfile --target development -t dht:dev .

# Run specific tests in Docker
docker-test-%:
	docker compose run --rm dht-test pytest -v --tb=short -k $*

# Build and push to registry (requires authentication)
docker-push: docker-build
	@echo "To push images, tag them appropriately and run:"
	@echo "  docker tag dht:runtime your-registry/dht:runtime"
	@echo "  docker push your-registry/dht:runtime"
