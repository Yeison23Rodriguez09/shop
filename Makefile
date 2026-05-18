# ─────────────────────────────────────────────────────────────────────────────
#  Nexo YR Secure — Makefile
#  Uso: make <target>
# ─────────────────────────────────────────────────────────────────────────────

PYTHON      := python
MANAGE      := $(PYTHON) manage.py
SETTINGS    := config.settings.development

.DEFAULT_GOAL := help

.PHONY: help install run shell migrate makemigrations createsuperuser \
        test test-cov lint format \
        sync-content sync-inventory export-inventory \
        cancel-expired-orders collectstatic \
        docker-up docker-down docker-prod-up

# ─── Ayuda ───────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Nexo YR Secure — comandos disponibles"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo "  install               Instala dependencias de desarrollo"
	@echo "  run                   Inicia el servidor de desarrollo"
	@echo "  shell                 Abre shell de Django"
	@echo "  migrate               Aplica migraciones pendientes"
	@echo "  makemigrations        Genera nuevas migraciones"
	@echo "  createsuperuser       Crea superusuario admin"
	@echo ""
	@echo "  test                  Ejecuta la suite de tests"
	@echo "  test-cov              Tests con reporte de cobertura"
	@echo "  lint                  Revisa estilo con flake8"
	@echo "  format                Aplica black + isort"
	@echo ""
	@echo "  sync-content          Sincroniza content/ → DB (estructura)"
	@echo "  sync-inventory        Carga inventario desde Excel (args: FILE=...)"
	@echo "  export-inventory      Exporta inventario a Excel (args: FILE=...)"
	@echo "  cancel-expired        Cancela pedidos expirados (default 48h)"
	@echo ""
	@echo "  docker-up             Levanta entorno Docker de desarrollo"
	@echo "  docker-down           Detiene contenedores Docker"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo ""

# ─── Entorno ─────────────────────────────────────────────────────────────────
install:
	pip install --upgrade pip
	pip install -r requirements/dev.txt

run:
	$(MANAGE) runserver

shell:
	$(MANAGE) shell_plus 2>/dev/null || $(MANAGE) shell

# ─── Migraciones ─────────────────────────────────────────────────────────────
migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

createsuperuser:
	$(MANAGE) createsuperuser

# ─── Tests ───────────────────────────────────────────────────────────────────
test:
	pytest

test-cov:
	pytest --cov=apps --cov-report=term-missing --cov-report=html

# ─── Calidad ─────────────────────────────────────────────────────────────────
lint:
	flake8 apps/ config/ --max-line-length=100 --exclude=migrations

format:
	black apps/ config/ scripts/
	isort apps/ config/ scripts/

# ─── Comandos de negocio ─────────────────────────────────────────────────────
sync-content:
	$(MANAGE) sync_content

# Uso: make sync-inventory FILE=inventario.xlsx
sync-inventory:
	$(MANAGE) sync_inventory_from_excel $(FILE)

# Uso: make export-inventory FILE=snapshot.xlsx
export-inventory:
	$(MANAGE) export_inventory_to_excel $(or $(FILE),media/exports/inventario_$(shell date +%Y%m%d).xlsx)

cancel-expired:
	$(MANAGE) cancel_expired_orders --hours=$(or $(HOURS),48)

collectstatic:
	$(MANAGE) collectstatic --noinput

# ─── Docker ──────────────────────────────────────────────────────────────────
docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-prod-up:
	docker compose -f docker-compose.prod.yml up --build -d
