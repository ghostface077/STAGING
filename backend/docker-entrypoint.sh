#!/bin/sh
# Point d'entrée de l'image backend : applique les migrations Alembic puis
# démarre l'API. Volontairement dans l'image (et non dans le `command:` de
# docker-compose) pour que ça fonctionne à l'identique quelle que soit la
# plateforme qui exécute cette image — y compris Render, qui construit et
# lance le Dockerfile directement, sans jamais lire docker-compose.prod.yml.
set -e

echo "[entrypoint] Application des migrations Alembic..."
alembic upgrade head

echo "[entrypoint] Démarrage d'uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
