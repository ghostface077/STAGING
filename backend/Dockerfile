# --- Dépendances : compilées ici, jamais dans l'image finale ---
# psycopg2-binary embarque déjà les binaires PostgreSQL, mais gcc/libpq-dev
# restent nécessaires pour certaines roues (wheels) sans binaire précompilé
# pour cette architecture. Isolés dans ce stage, ils ne pèsent jamais dans
# l'image d'exécution.
FROM python:3.12-slim AS deps

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Exécution : image finale minimale, sans outils de compilation ---
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH

# curl : nécessaire au HEALTHCHECK ci-dessous (interrogation de /api/health).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

COPY --from=deps --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

RUN mkdir -p /app/uploads \
    && chown appuser:appuser /app/uploads \
    && chmod +x /app/docker-entrypoint.sh

USER appuser

EXPOSE 8000

# ${PORT:-8000} et non 8000 en dur : sur Render, l'entrypoint écoute sur le
# port que $PORT désigne (voir docker-entrypoint.sh) — un port fixe ici
# ferait échouer ce healthcheck dès que $PORT diffère de 8000.
#
# start-period=90s (et non 20s) : l'entrypoint exécute `alembic upgrade head`
# puis, hors production, `python -m app.seed` AVANT de lancer uvicorn (voir
# docker-entrypoint.sh) — mesuré à ~90-120s à froid (migrations + seed des
# données de démonstration) selon la charge de la machine hôte, largement
# au-delà de l'ancien budget de 20s+5×15s=95s. Ce budget trop court faisait
# marquer le conteneur "unhealthy" alors que l'API démarrait normalement,
# juste trop tard pour les vérifications déjà toutes épuisées — ce qui
# bloquait ensuite `nginx`/`frontend` via leur `depends_on: service_healthy`.
# retries=6 : les vérifications après le start-period gardent 60s de marge
# supplémentaire (6×10s) pour absorber un démarrage encore plus lent.
HEALTHCHECK --interval=10s --timeout=5s --start-period=90s --retries=6 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
