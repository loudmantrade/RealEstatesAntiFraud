# Makefile for RealEstatesAntiFraud

.PHONY: help dev test install-plugins build migrate seed clean lint format plugin-install

# Colors for output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

help: ## Show this help message
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-20s${GREEN}%s${RESET}\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development
dev: ## Run in development mode
	@echo "${GREEN}Starting development environment...${RESET}"
	docker-compose up -d
	@echo "${GREEN}Waiting for services to be ready...${RESET}"
	sleep 5
	@echo "${GREEN}Starting API server...${RESET}"
	cd core && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-stop: ## Stop development environment
	@echo "${YELLOW}Stopping development environment...${RESET}"
	docker-compose down

dev-logs: ## Show logs from all services
	docker-compose logs -f

# Setup
setup: ## Initial setup (install dependencies, create DB, install plugins)
	@echo "${GREEN}Setting up RealEstatesAntiFraud...${RESET}"
	@make install-deps
	@make docker-up
	@make migrate
	@make install-default-plugins
	@echo "${GREEN}Setup complete!${RESET}"

install-deps: ## Install Python dependencies
	@echo "${GREEN}Installing Python dependencies...${RESET}"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-deps-frontend: ## Install frontend dependencies
	@echo "${GREEN}Installing frontend dependencies...${RESET}"
	cd frontend/web && npm install
	cd frontend/admin && npm install

# Docker
docker-up: ## Start Docker containers
	@echo "${GREEN}Starting Docker containers...${RESET}"
	docker-compose up -d

docker-down: ## Stop Docker containers
	@echo "${YELLOW}Stopping Docker containers...${RESET}"
	docker-compose down

docker-down-v: ## Stop Docker containers and remove volumes
	@echo "${YELLOW}Stopping Docker containers and removing volumes...${RESET}"
	docker-compose down -v

docker-rebuild: ## Rebuild Docker images
	@echo "${GREEN}Rebuilding Docker images...${RESET}"
	docker-compose build --no-cache

docker-ps: ## Show running containers
	docker-compose ps

# Database
migrate: ## Run database migrations
	@echo "${GREEN}Running database migrations...${RESET}"
	python scripts/migrate_database.py

migrate-create: ## Create new migration (usage: make migrate-create name=migration_name)
	@echo "${GREEN}Creating new migration: $(name)${RESET}"
	python scripts/create_migration.py $(name)

seed: ## Seed database with test data
	@echo "${GREEN}Seeding database...${RESET}"
	python scripts/seed_data.py

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "${YELLOW}Resetting database...${RESET}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d; \
		sleep 5; \
		make migrate; \
		make seed; \
	fi

# Plugins
install-default-plugins: ## Install default plugins
	@echo "${GREEN}Installing default plugins...${RESET}"
	python scripts/install_plugin.py plugins/sources/avito
	python scripts/install_plugin.py plugins/sources/cian
	python scripts/install_plugin.py plugins/processing/normalizer
	python scripts/install_plugin.py plugins/processing/geocoder
	python scripts/install_plugin.py plugins/detection/ml-classifier
	python scripts/install_plugin.py plugins/detection/rules-engine
	python scripts/install_plugin.py plugins/search/elasticsearch

plugin-install: ## Install plugin (usage: make plugin-install path=./plugins/sources/new-source)
	@echo "${GREEN}Installing plugin from $(path)...${RESET}"
	python scripts/install_plugin.py $(path)

plugin-list: ## List installed plugins
	@echo "${GREEN}Installed plugins:${RESET}"
	python scripts/list_plugins.py

plugin-validate: ## Validate plugin (usage: make plugin-validate path=./plugins/sources/new-source)
	@echo "${GREEN}Validating plugin at $(path)...${RESET}"
	python scripts/validate_plugin.py $(path)

plugin-create: ## Create new plugin from template (usage: make plugin-create type=source name=example)
	@echo "${GREEN}Creating new $(type) plugin: $(name)${RESET}"
	python scripts/create_plugin.py --type $(type) --name $(name)

# Testing
test: ## Run all tests
	@echo "${GREEN}Running tests...${RESET}"
	pytest tests/ -v --cov=core --cov=plugins --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	@echo "${GREEN}Running unit tests...${RESET}"
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "${GREEN}Running integration tests...${RESET}"
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	@echo "${GREEN}Running e2e tests...${RESET}"
	pytest tests/e2e/ -v

test-coverage: ## Generate test coverage report
	@echo "${GREEN}Generating coverage report...${RESET}"
	pytest tests/ --cov=core --cov=plugins --cov-report=html
	@echo "${GREEN}Coverage report generated in htmlcov/index.html${RESET}"

# Code Quality
lint: ## Run linters
	@echo "${GREEN}Running linters...${RESET}"
	flake8 core/ plugins/ --max-line-length=120
	pylint core/ plugins/
	mypy core/ plugins/

format: ## Format code with black
	@echo "${GREEN}Formatting code...${RESET}"
	black core/ plugins/ tests/ scripts/
	isort core/ plugins/ tests/ scripts/

format-check: ## Check code formatting
	@echo "${GREEN}Checking code formatting...${RESET}"
	black --check core/ plugins/ tests/ scripts/
	isort --check core/ plugins/ tests/ scripts/

security-scan: ## Run security vulnerability scan
	@echo "${GREEN}Scanning for security vulnerabilities...${RESET}"
	bandit -r core/ plugins/
	safety check

# Frontend
frontend-dev: ## Run frontend in development mode
	@echo "${GREEN}Starting frontend dev server...${RESET}"
	cd frontend/web && npm run dev

frontend-build: ## Build frontend for production
	@echo "${GREEN}Building frontend...${RESET}"
	cd frontend/web && npm run build

frontend-test: ## Run frontend tests
	@echo "${GREEN}Running frontend tests...${RESET}"
	cd frontend/web && npm test

admin-dev: ## Run admin dashboard in development mode
	@echo "${GREEN}Starting admin dashboard dev server...${RESET}"
	cd frontend/admin && npm run dev

# ML Models
ml-train: ## Train fraud detection model
	@echo "${GREEN}Training fraud detection model...${RESET}"
	python ml-models/fraud-detection/scripts/train.py

ml-evaluate: ## Evaluate ML model
	@echo "${GREEN}Evaluating ML model...${RESET}"
	python ml-models/fraud-detection/scripts/evaluate.py

ml-deploy: ## Deploy ML model
	@echo "${GREEN}Deploying ML model...${RESET}"
	python ml-models/fraud-detection/scripts/deploy.py

mlflow-ui: ## Start MLflow UI
	@echo "${GREEN}Starting MLflow UI...${RESET}"
	cd ml-models && mlflow ui

# Monitoring
logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api-gateway

logs-scraper: ## Show scraper logs
	docker-compose logs -f scraper-service

logs-detection: ## Show detection service logs
	docker-compose logs -f detection-service

prometheus: ## Open Prometheus UI
	@echo "${GREEN}Opening Prometheus UI...${RESET}"
	open http://localhost:9090

grafana: ## Open Grafana UI
	@echo "${GREEN}Opening Grafana UI...${RESET}"
	open http://localhost:3001

kibana: ## Open Kibana UI
	@echo "${GREEN}Opening Kibana UI...${RESET}"
	open http://localhost:5601

# Production
build-prod: ## Build production Docker images
	@echo "${GREEN}Building production images...${RESET}"
	docker-compose -f docker-compose.prod.yml build

deploy-prod: ## Deploy to production
	@echo "${YELLOW}Deploying to production...${RESET}"
	./scripts/deploy.sh production

deploy-staging: ## Deploy to staging
	@echo "${YELLOW}Deploying to staging...${RESET}"
	./scripts/deploy.sh staging

# Kubernetes
k8s-deploy: ## Deploy to Kubernetes
	@echo "${GREEN}Deploying to Kubernetes...${RESET}"
	kubectl apply -f infrastructure/kubernetes/

k8s-delete: ## Delete from Kubernetes
	@echo "${YELLOW}Deleting from Kubernetes...${RESET}"
	kubectl delete -f infrastructure/kubernetes/

k8s-status: ## Show Kubernetes deployment status
	kubectl get pods,services,deployments -n realestate

helm-install: ## Install with Helm
	@echo "${GREEN}Installing with Helm...${RESET}"
	helm install realestate infrastructure/kubernetes/helm/realestate

helm-upgrade: ## Upgrade Helm release
	@echo "${GREEN}Upgrading Helm release...${RESET}"
	helm upgrade realestate infrastructure/kubernetes/helm/realestate

# Utilities
clean: ## Clean up temporary files and caches
	@echo "${YELLOW}Cleaning up...${RESET}"
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "${GREEN}Cleanup complete!${RESET}"

backup: ## Backup database
	@echo "${GREEN}Backing up database...${RESET}"
	./scripts/backup.sh

restore: ## Restore database from backup (usage: make restore file=backup.sql)
	@echo "${GREEN}Restoring database from $(file)...${RESET}"
	./scripts/restore.sh $(file)

shell: ## Open Python shell with app context
	@echo "${GREEN}Opening Python shell...${RESET}"
	python scripts/shell.py

db-shell: ## Open database shell
	@echo "${GREEN}Opening PostgreSQL shell...${RESET}"
	docker-compose exec postgres psql -U realestate -d realestate

redis-cli: ## Open Redis CLI
	@echo "${GREEN}Opening Redis CLI...${RESET}"
	docker-compose exec redis redis-cli

# Documentation
docs-serve: ## Serve documentation locally
	@echo "${GREEN}Serving documentation...${RESET}"
	cd docs && python -m http.server 8080

docs-build: ## Build API documentation
	@echo "${GREEN}Building API documentation...${RESET}"
	python scripts/generate_api_docs.py

# CI/CD
ci: lint test ## Run CI pipeline locally
	@echo "${GREEN}Running CI pipeline...${RESET}"

# Default target
.DEFAULT_GOAL := help
