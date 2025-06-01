# Project GeminiVoiceConnect - Comprehensive Build and Deployment Makefile
# Revolutionary AI Call Center Agent Generation System

.PHONY: help build start stop restart logs clean test deploy generate-modems setup-gpu check-deps

# Default target
help: ## Show this help message
	@echo "Project GeminiVoiceConnect - AI Call Center Agent"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment variables
COMPOSE_PROJECT_NAME := geminivoiceconnect
DOCKER_BUILDKIT := 1
COMPOSE_DOCKER_CLI_BUILD := 1

# Check dependencies
check-deps: ## Check system dependencies
	@echo "Checking system dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }
	@command -v nvidia-smi >/dev/null 2>&1 || { echo "NVIDIA GPU drivers are required but not found. Aborting." >&2; exit 1; }
	@echo "✓ All dependencies satisfied"

# Setup GPU support
setup-gpu: ## Setup NVIDIA GPU support for Docker
	@echo "Setting up NVIDIA GPU support..."
	@docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi || { echo "GPU setup failed. Check NVIDIA Docker runtime." >&2; exit 1; }
	@echo "✓ GPU support verified"

# Generate modem daemon configurations
generate-modems: ## Generate Docker Compose configuration for 80 modem daemons
	@echo "Generating modem daemon configurations..."
	@python3 scripts/generate_modem_compose.py
	@echo "✓ Generated docker-compose.modems.yml with 80 modem instances"

# Build all services
build: check-deps ## Build all Docker images
	@echo "Building all services..."
	@DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build --parallel
	@echo "✓ All services built successfully"

# Build specific service
build-%: ## Build specific service (e.g., make build-voice-bridge)
	@echo "Building $* service..."
	@DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose build $*
	@echo "✓ $* service built successfully"

# Start core services
start: check-deps setup-gpu ## Start core services (without modems)
	@echo "Starting core services..."
	@docker-compose up -d redis postgres
	@echo "Waiting for database to be ready..."
	@sleep 10
	@docker-compose up -d voice-bridge core-api task-runner dashboard traefik prometheus grafana
	@echo "✓ Core services started successfully"
	@echo ""
	@echo "Services available at:"
	@echo "  Dashboard:     http://localhost:3000"
	@echo "  Core API:      http://localhost:8001"
	@echo "  Voice Bridge:  http://localhost:8000"
	@echo "  Traefik:       http://localhost:8080"
	@echo "  Prometheus:    http://localhost:9090"
	@echo "  Grafana:       http://localhost:3001"

# Start with modems
start-full: start generate-modems ## Start all services including 80 modem daemons
	@echo "Starting modem daemons..."
	@docker-compose -f docker-compose.modems.yml up -d
	@echo "✓ All services including modems started successfully"

# Stop all services
stop: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down
	@docker-compose -f docker-compose.modems.yml down 2>/dev/null || true
	@echo "✓ All services stopped"

# Restart services
restart: stop start ## Restart all core services

# View logs
logs: ## View logs from all services
	@docker-compose logs -f

# View logs for specific service
logs-%: ## View logs for specific service (e.g., make logs-voice-bridge)
	@docker-compose logs -f $*

# Clean up everything
clean: stop ## Clean up containers, volumes, and images
	@echo "Cleaning up..."
	@docker-compose down -v --remove-orphans
	@docker-compose -f docker-compose.modems.yml down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@echo "✓ Cleanup completed"

# Deep clean including images
clean-all: clean ## Deep clean including all images and build cache
	@echo "Performing deep clean..."
	@docker-compose down --rmi all -v --remove-orphans
	@docker builder prune -f
	@echo "✓ Deep clean completed"

# Run tests
test: ## Run comprehensive test suite
	@echo "Running test suite..."
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down -v
	@echo "✓ Tests completed"

# Test specific service
test-%: ## Test specific service (e.g., make test-voice-bridge)
	@echo "Testing $* service..."
	@docker-compose exec $* python -m pytest tests/ -v
	@echo "✓ $* tests completed"

# Development mode
dev: ## Start services in development mode with hot reload
	@echo "Starting development environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "✓ Development environment started"

# Production deployment
deploy: check-deps build ## Deploy to production environment
	@echo "Deploying to production..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✓ Production deployment completed"

# Health check
health: ## Check health of all services
	@echo "Checking service health..."
	@docker-compose ps
	@echo ""
	@echo "Detailed health status:"
	@curl -s http://localhost:8001/health | jq '.' 2>/dev/null || echo "Core API health check failed"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "Voice Bridge health check failed"

# Monitor services
monitor: ## Open monitoring dashboard
	@echo "Opening monitoring dashboard..."
	@open http://localhost:3001 2>/dev/null || xdg-open http://localhost:3001 2>/dev/null || echo "Please open http://localhost:3001 in your browser"

# Backup data
backup: ## Backup all persistent data
	@echo "Creating backup..."
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@docker run --rm -v geminivoiceconnect_postgres_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
	@docker run --rm -v geminivoiceconnect_redis_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
	@echo "✓ Backup completed in backups/$(shell date +%Y%m%d_%H%M%S)"

# Restore data
restore: ## Restore data from backup (specify BACKUP_DIR)
	@if [ -z "$(BACKUP_DIR)" ]; then echo "Please specify BACKUP_DIR=path/to/backup"; exit 1; fi
	@echo "Restoring from $(BACKUP_DIR)..."
	@docker run --rm -v geminivoiceconnect_postgres_data:/data -v $(PWD)/$(BACKUP_DIR):/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
	@docker run --rm -v geminivoiceconnect_redis_data:/data -v $(PWD)/$(BACKUP_DIR):/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
	@echo "✓ Restore completed"

# Update services
update: ## Update all services to latest versions
	@echo "Updating services..."
	@docker-compose pull
	@docker-compose up -d
	@echo "✓ Services updated"

# Scale specific service
scale-%: ## Scale specific service (e.g., make scale-task-runner REPLICAS=3)
	@if [ -z "$(REPLICAS)" ]; then echo "Please specify REPLICAS=number"; exit 1; fi
	@echo "Scaling $* to $(REPLICAS) replicas..."
	@docker-compose up -d --scale $*=$(REPLICAS)
	@echo "✓ $* scaled to $(REPLICAS) replicas"

# Generate SSL certificates
ssl: ## Generate SSL certificates for production
	@echo "Generating SSL certificates..."
	@mkdir -p ssl
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout ssl/private.key \
		-out ssl/certificate.crt \
		-subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
	@echo "✓ SSL certificates generated in ssl/"

# Database operations
db-migrate: ## Run database migrations
	@echo "Running database migrations..."
	@docker-compose exec core-api alembic upgrade head
	@echo "✓ Database migrations completed"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "WARNING: This will delete all database data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; echo; if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose stop postgres; \
		docker volume rm geminivoiceconnect_postgres_data; \
		docker-compose up -d postgres; \
		sleep 10; \
		make db-migrate; \
		echo "✓ Database reset completed"; \
	else \
		echo "Database reset cancelled"; \
	fi

# Performance testing
perf-test: ## Run performance tests
	@echo "Running performance tests..."
	@docker run --rm --network geminivoiceconnect_gemini-network \
		-v $(PWD)/tests/performance:/tests \
		loadimpact/k6:latest run /tests/load_test.js
	@echo "✓ Performance tests completed"

# Security scan
security-scan: ## Run security vulnerability scan
	@echo "Running security scan..."
	@docker run --rm -v $(PWD):/app -w /app securecodewarrior/docker-security-scan
	@echo "✓ Security scan completed"

# Generate documentation
docs: ## Generate comprehensive documentation
	@echo "Generating documentation..."
	@docker run --rm -v $(PWD):/docs -w /docs squidfunk/mkdocs-material build
	@echo "✓ Documentation generated in site/"

# Serve documentation
docs-serve: ## Serve documentation locally
	@echo "Serving documentation at http://localhost:8000"
	@docker run --rm -p 8000:8000 -v $(PWD):/docs -w /docs squidfunk/mkdocs-material serve -a 0.0.0.0:8000

# Install development dependencies
install-dev: ## Install development dependencies
	@echo "Installing development dependencies..."
	@pip install -r requirements-dev.txt
	@npm install -g @commitlint/cli @commitlint/config-conventional
	@echo "✓ Development dependencies installed"

# Format code
format: ## Format all code
	@echo "Formatting code..."
	@docker run --rm -v $(PWD):/app -w /app python:3.12 bash -c "pip install black isort && black . && isort ."
	@docker run --rm -v $(PWD)/dashboard:/app -w /app node:18 bash -c "npm install prettier && npx prettier --write ."
	@echo "✓ Code formatting completed"

# Lint code
lint: ## Lint all code
	@echo "Linting code..."
	@docker run --rm -v $(PWD):/app -w /app python:3.12 bash -c "pip install flake8 mypy && flake8 . && mypy ."
	@docker run --rm -v $(PWD)/dashboard:/app -w /app node:18 bash -c "npm install eslint && npx eslint ."
	@echo "✓ Code linting completed"

# Git hooks
install-hooks: ## Install Git hooks for development
	@echo "Installing Git hooks..."
	@cp scripts/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@cp scripts/commit-msg .git/hooks/commit-msg
	@chmod +x .git/hooks/commit-msg
	@echo "✓ Git hooks installed"

# Environment setup
setup-env: ## Setup development environment
	@echo "Setting up development environment..."
	@cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "✓ Environment setup completed"

# Quick start
quick-start: setup-env build start ## Quick start for new developers
	@echo ""
	@echo "🚀 GeminiVoiceConnect is now running!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Visit http://localhost:3000 for the dashboard"
	@echo "3. Check http://localhost:8001/docs for API documentation"
	@echo "4. Monitor services at http://localhost:3001 (Grafana)"
	@echo ""
	@echo "For full deployment with modems: make start-full"