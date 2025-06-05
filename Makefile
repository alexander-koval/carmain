.PHONY: help dev prod build-prod up-prod down-prod logs clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start development environment
	docker-compose -f docker-compose.dev.yml up --build

prod: ## Start production environment
	docker-compose -f docker-compose.prod.yml up -d

build-prod: ## Build production images
	docker-compose -f docker-compose.prod.yml build --no-cache

up-prod: ## Start production services (detached)
	docker-compose -f docker-compose.prod.yml up -d

down-prod: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

logs-web: ## Show web service logs
	docker-compose -f docker-compose.prod.yml logs -f web

clean: ## Clean up containers and volumes
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

backup-db: ## Backup production database
	docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U $$POSTGRES_USER $$DB_NAME > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database from backup (usage: make restore-db BACKUP=backup_file.sql)
	docker-compose -f docker-compose.prod.yml exec -T postgres psql -U $$POSTGRES_USER $$DB_NAME < $(BACKUP)

# Docker Registry Commands
GITHUB_USERNAME ?= yourusername
IMAGE_NAME = ghcr.io/$(GITHUB_USERNAME)/carmain

docker-login: ## Login to GitHub Container Registry
	echo $$GITHUB_TOKEN | docker login ghcr.io -u $(GITHUB_USERNAME) --password-stdin

docker-build-push: ## Build and push image to GitHub Container Registry
	docker build -f Dockerfile.prod -t $(IMAGE_NAME):latest .
	docker push $(IMAGE_NAME):latest

docker-build-tag: ## Build and push with version tag (usage: make docker-build-tag VERSION=v1.0.0)
	docker build -f Dockerfile.prod -t $(IMAGE_NAME):$(VERSION) -t $(IMAGE_NAME):latest .
	docker push $(IMAGE_NAME):$(VERSION)
	docker push $(IMAGE_NAME):latest

# Docker Hub Commands
DOCKERHUB_USERNAME ?= yourusername
DOCKERHUB_IMAGE = $(DOCKERHUB_USERNAME)/carmain

dockerhub-login: ## Login to Docker Hub
	docker login

dockerhub-build-push: ## Build and push to Docker Hub
	docker build -f Dockerfile.prod -t $(DOCKERHUB_IMAGE):latest .
	docker push $(DOCKERHUB_IMAGE):latest