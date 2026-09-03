#!/bin/sh
# Point d'entrée de l'image backend : applique les migrations Alembic, injecte
# les données de démonstration si pertinent, puis démarre l'API. Volontairement
# dans l'image (et non dans le `command:` de docker-compose) pour que ça
# fonctionne à l'identique quelle que soit la plateforme qui exécute cette
# image — y compris Render, qui construit et lance le Dockerfile directement,
# sans jamais lire de fichier docker-compose.
set -e

echo "[entrypoint] Application des migrations Alembic..."
alembic upgrade head

# Miroir de la règle appliquée par app/config.py (_validate_production_secrets) :
# le seed ne doit jamais tourner en production, et peut être désactivé
# explicitement ailleurs via SEED_ON_STARTUP=false.
if [ "$ENVIRONMENT" != "production" ] && [ "$SEED_ON_STARTUP" != "false" ]; then
    echo "[entrypoint] Environnement non-production : injection des données de démonstration..."
    python -m app.seed
else
    echo "[entrypoint] Production ou SEED_ON_STARTUP=false : seed ignoré."
fi

echo "[entrypoint] Démarrage d'uvicorn..."
# Render assigne dynamiquement le port d'écoute via $PORT et route son proxy
# vers cette valeur précise (pas nécessairement 8000) : un port codé en dur
# ici ferait échouer toute requête entrante avec un 502, même conteneur en
# bonne santé. ${PORT:-8000} : conserve 8000 par défaut pour docker-compose
# (local/VPS), où PORT n'est jamais défini.
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
