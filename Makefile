UV := docker compose run -u $(USERID):$(GROUPID) --rm django uv
PYTHON := $(UV) run
DOCKER_COMPOSE := docker compose

.PHONY: help up down build logs shell test format lint check install clean reset-db

help:
	@echo "Available commands:"
	@echo "  up                - Start all services"
	@echo "  down              - Stop all services"
	@echo "  build             - Build docker images"
	@echo "  logs              - Show logs"
	@echo "  restart           - Restart all services"
	@echo "  shell             - Enter Django shell"
	@echo "  bash              - Enter container bash"
	@echo "  dbshell           - Enter PostgreSQL shell"
	@echo "  test              - Run tests"
	@echo "  test-coverage     - Run tests with coverage"
	@echo "  format            - Format code with ruff"
	@echo "  lint              - Check code with ruff"
	@echo "  check             - Run all checks (lint + test)"
	@echo "  install           - Install dependencies"
	@echo "  makemigrations    - Create migrations"
	@echo "  migrate           - Apply migrations"
	@echo "  createsuperuser   - Create superuser"
	@echo "  collectstatic     - Collect static files"
	@echo "  startapp          - Create new app (use: make startapp app=myapp)"
	@echo "  reset-db          - Reset database"
	@echo "  clean             - Clean up containers and volumes"

up:
	$(DOCKER_COMPOSE) up

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

logs:
	$(DOCKER_COMPOSE) logs -f

restart:
	$(DOCKER_COMPOSE) restart

bash:
	$(DOCKER_COMPOSE) exec django bash

dbshell:
	$(PYTHON) manage.py dbshell

collectstatic:
	$(PYTHON) manage.py collectstatic --noi -c

startapp:
	$(PYTHON) manage.py startapp ${app}

makemigrations:
	$(PYTHON) manage.py makemigrations ${app}

migrate:
	$(PYTHON) manage.py migrate ${app}

createsuperuser:
	$(PYTHON) manage.py createsuperuser

shell:
	$(PYTHON) manage.py shell_plus

reset-db:
	$(PYTHON) manage.py reset_db

format:
	$(PYTHON) ruff check --fix --unsafe-fixes . && $(PYTHON) ruff check --select I --fix --unsafe-fixes . && $(PYTHON) ruff format .

lint:
	uvx ruff check apps config

check: lint test

install:
	$(UV) sync

list_packages:
	$(UV) pip list

test:
	$(PYTHON) pytest -v

test-coverage:
	$(PYTHON) pytest -v --cov=apps --cov-report=html --cov-report=term

clean:
	$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans
	docker system prune -f
