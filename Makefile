.PHONY: help up down logs backend-test backend-lint migrate downgrade

# Default target
help:
	@echo "Available commands:"
	@echo "  up          - Start all services with docker compose"
	@echo "  down        - Stop all services"
	@echo "  logs        - Show logs for all services"
	@echo "  migrate     - Run database migrations"
	@echo "  downgrade   - Rollback last migration"
	@echo "  backend-test - Run backend tests"
	@echo "  backend-lint - Lint and format backend code"
	@echo "  frontend-test - Run frontend tests"
	@echo "  clean       - Clean docker containers and volumes"

# Docker commands
up:
	docker compose up -d
	@echo "Services started. Frontend: http://localhost:3000"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	docker system prune -f

# Database commands
migrate:
	docker compose exec backend alembic upgrade head

downgrade:
	docker compose exec backend alembic downgrade -1

# Backend commands
backend-test:
	docker compose exec backend pytest -v
	docker compose exec backend pytest --cov=app --cov-report=term-missing

backend-lint:
	docker compose exec backend ruff check .
	docker compose exec backend ruff format .
	docker compose exec backend black --check .

backend-format:
	docker compose exec backend ruff format .
	docker compose exec backend black .

# Frontend commands
frontend-test:
	docker compose exec frontend npm test

frontend-build:
	docker compose exec frontend npm run build

# Development commands
dev-backend:
	cd backend && python -m app.main

dev-frontend:
	cd frontend && npm run dev

# Database reset
reset-db:
	docker compose down -v
	docker compose up -d postgres redis
	sleep 5
	docker compose exec backend alembic upgrade head
	@echo "Database reset complete"

# Shell access
shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U postgres -d addressable
