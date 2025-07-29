.PHONY: help install test lint format run docker-build docker-up docker-down clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)LLM Template Backend - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)Dependencies installed!$(NC)"

test: ## Run all tests with coverage
	@echo "$(YELLOW)Running tests...$(NC)"
	$(PYTEST) tests/ -v --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Tests completed! Coverage report available in htmlcov/index.html$(NC)"

test-unit: ## Run unit tests only
	@echo "$(YELLOW)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	@echo "$(YELLOW)Running e2e tests...$(NC)"
	$(PYTEST) tests/e2e/ -v

lint: ## Run linting checks
	@echo "$(YELLOW)Running linters...$(NC)"
	$(FLAKE8) app tests
	$(MYPY) app
	@echo "$(GREEN)Linting passed!$(NC)"

format: ## Format code with black
	@echo "$(YELLOW)Formatting code...$(NC)"
	$(BLACK) app tests
	@echo "$(GREEN)Code formatted!$(NC)"

run: ## Run the application locally
	@echo "$(YELLOW)Starting application...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-celery: ## Run Celery worker
	@echo "$(YELLOW)Starting Celery worker...$(NC)"
	celery -A app.celery_app worker --loglevel=info

run-celery-beat: ## Run Celery beat scheduler
	@echo "$(YELLOW)Starting Celery beat...$(NC)"
	celery -A app.celery_app beat --loglevel=info

run-flower: ## Run Flower for Celery monitoring
	@echo "$(YELLOW)Starting Flower...$(NC)"
	celery -A app.celery_app flower

docker-build: ## Build Docker images
	@echo "$(YELLOW)Building Docker images...$(NC)"
	docker-compose build
	@echo "$(GREEN)Docker images built!$(NC)"

docker-up: ## Start all services with Docker Compose
	@echo "$(YELLOW)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started! API available at http://localhost:8000$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	docker-compose down
	@echo "$(GREEN)Services stopped!$(NC)"

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	docker-compose down -v
	docker system prune -f
	@echo "$(GREEN)Docker resources cleaned!$(NC)"

db-shell: ## Access MongoDB shell
	docker exec -it llm_template_mongodb mongosh

redis-cli: ## Access Redis CLI
	docker exec -it llm_template_redis redis-cli

migrate: ## Run database migrations (if any)
	@echo "$(YELLOW)Running migrations...$(NC)"
	$(PYTHON) -m app.migrate
	@echo "$(GREEN)Migrations completed!$(NC)"

clean: ## Clean up temporary files
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "$(GREEN)Cleanup completed!$(NC)"

pre-commit: format lint test ## Run all pre-commit checks
	@echo "$(GREEN)All pre-commit checks passed!$(NC)"

prod-deploy: ## Deploy to production
	@echo "$(YELLOW)Deploying to production...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "$(GREEN)Production deployment completed!$(NC)"

backup: ## Backup database
	@echo "$(YELLOW)Creating database backup...$(NC)"
	docker exec llm_template_mongodb mongodump --out /backup/$(shell date +%Y%m%d_%H%M%S)
	@echo "$(GREEN)Backup completed!$(NC)"

restore: ## Restore database from backup
	@echo "$(YELLOW)Restoring database...$(NC)"
	@read -p "Enter backup directory name: " backup_dir; \
	docker exec llm_template_mongodb mongorestore /backup/$$backup_dir
	@echo "$(GREEN)Restore completed!$(NC)"

logs: ## Show application logs
	tail -f logs/app.log

version: ## Show version information
	@echo "$(BLUE)LLM Template Backend$(NC)"
	@echo "Version: $(shell grep 'app_version' app/config.py | cut -d'"' -f2)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "FastAPI: $(shell $(PIP) show fastapi | grep Version)"

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		echo "$(YELLOW)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN).env file created. Please update it with your settings.$(NC)"; \
	else \
		echo "$(GREEN).env file exists!$(NC)"; \
	fi