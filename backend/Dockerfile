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

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
