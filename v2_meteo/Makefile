# ==============================================================================
# PROJET : Météo Marine Marseille

# UTILITÉ : Automatisation des tâches (Installation, Collecte, ML, Docker)

# DESCRIPTION : 
# Ce Makefile centralise toutes les commandes pour faciliter le développement et le déploiement.
# Il permet d'exécuter les scripts Python, de gérer les dépendances avec uv, et de construire/lancer des conteneurs Docker.


# COMMANDES :
# - make help           : Affiche les commandes disponibles

# - make install        : Installe les dépendances avec uv

# - make run            : Exécute le pipeline principal (module src.pipeline)
# - make collect        : Récupère les données (module src.collect)
# - make consolidate    : Consolide les données (module src.consolidate)
# - make split          : Crée les splits train/val/test (module src.split)

# - make docker-build     	: Build l'image Docker
# - make docker-run       	: Lance le conteneur Docker
# - make docker-collect    	: Récupère les données dans un conteneur Docker
# - make docker-consolidate : Consolide les données dans un conteneur Docker
# - make docker-clean   	: Supprime les conteneurs/images Docker

# - make lint           : Vérifie le code avec black et ruff
# - make format         : Formate le code avec black et ruff
# - make test           : Exécute les tests avec pytest

# - make clean          : Nettoie les fichiers temporaires et caches


# AUTEUR : Bruno Coulet
# ==============================================================================


.PHONY: help install run collect consolidate split docker-build docker-run docker-collect docker-consolidate docker-split docker-clean

help:
	@echo "=== Commandes disponibles ==="
	@echo "Local (avec uv):"
	@echo "  make install          Installe les dépendances"
	@echo "  make run              Exécute le pipeline complet"
	@echo "  make collect          Récupère les données"
	@echo "  make consolidate      Consolide les données"
	@echo "  make split            Crée les splits train/val/test"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build l'image Docker"
	@echo "  make docker-run       Lance le conteneur"
	@echo "  make docker-collect   Collecte les données (Docker Compose)"
	@echo "  make docker-consolidate Consolide les données (Docker Compose)"
	@echo "  make docker-split     Crée les splits ML (Docker Compose)"
	@echo "  make docker-clean     Supprime les conteneurs/images"

# Installation
install:
	uv sync

# Exécution locale
run:
	uv run -m src.pipeline

collect:
	uv run -m src.collect

consolidate:
	uv run -m src.consolidate

split:
	uv run -m src.split

# Docker
docker-build:
	docker build -t open_meteo:latest .

docker-run:
	docker run --rm -v $(PWD)/data:/app/data open_meteo:latest

docker-collect:
	docker compose -f ../docker-compose.orchestration.yml run --rm meteo_marine_collect

docker-consolidate:
	docker compose -f ../docker-compose.orchestration.yml run --rm meteo_marine_collect

docker-split:
	docker compose -f ../docker-compose.orchestration.yml run --rm maritime_model

docker-clean:
	docker compose -f ../docker-compose.orchestration.yml down
	docker rmi open_meteo:latest 2>/dev/null || true

# Développement
lint:
	uv run black --check .
	uv run ruff check .

format:
	uv run black .
	uv run ruff check --fix .

test:
	uv run pytest -v

# Nettoyage
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage

