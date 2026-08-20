#!/usr/bin/env bash
# Sauvegarde la base PostgreSQL de production vers un fichier .sql horodaté
# dans backups/ (ignoré par Git). Équivalent bash de backup-postgres.ps1,
# utilisé notamment par le workflow GitHub Actions.
#
# Usage :
#   ./scripts/backup-postgres.sh                              # conteneur Docker local
#   DATABASE_URL="postgresql://..." ./scripts/backup-postgres.sh   # base distante (ex. Neon)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/../backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
OUT_FILE="$BACKUP_DIR/itsupport_$TIMESTAMP.sql"

if [ -n "${DATABASE_URL:-}" ]; then
    echo "Sauvegarde depuis une base distante (DATABASE_URL fourni)..."
    docker run --rm postgres:16-alpine pg_dump --no-owner --clean --if-exists "$DATABASE_URL" > "$OUT_FILE"
else
    echo "Sauvegarde du conteneur Docker local 'itsupport_db'..."
    docker exec itsupport_db pg_dump -U itsupport --no-owner --clean --if-exists itsupport_db > "$OUT_FILE"
fi

if [ ! -s "$OUT_FILE" ]; then
    echo "Échec de la sauvegarde — fichier vide ou absent : $OUT_FILE" >&2
    exit 1
fi

echo "Sauvegarde écrite : $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"
