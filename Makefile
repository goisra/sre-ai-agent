.PHONY: install dev test lint format build up down

install: ## Install backend (+ agent core, editable) and frontend dependencies
	pip install -e . -r backend/requirements-dev.txt
	cd frontend && npm install

dev: ## Run backend (Django dev server) and frontend (Vite dev server) locally
	@echo "Run these in two terminals:"
	@echo "  cd backend && python manage.py runserver"
	@echo "  cd frontend && npm run dev"

test: ## Run backend and frontend test suites
	cd backend && pytest
	cd frontend && npm run test

lint: ## Lint backend (ruff) and frontend (eslint)
	ruff check agent backend --exclude "*/migrations/*"
	cd frontend && npm run lint

format: ## Auto-format backend (ruff) and frontend (prettier)
	ruff format agent backend --exclude "*/migrations/*"
	cd frontend && npm run format

build: ## Build all Docker images
	docker compose build

up: ## Start the full stack (Postgres, backend, frontend)
	docker compose up --build

down: ## Stop the full stack
	docker compose down
