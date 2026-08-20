# Sauvegarde la base PostgreSQL de production (conteneur Docker `itsupport_db`
# ou instance Neon) vers un fichier .sql horodaté dans backups/ (ignoré par Git).
#
# Usage :
#   .\scripts\backup-postgres.ps1                     # sauvegarde le conteneur Docker local
#   .\scripts\backup-postgres.ps1 -DatabaseUrl "postgresql://..."   # sauvegarde une base distante (ex. Neon)

param(
    [string]$DatabaseUrl = $null
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = Join-Path $PSScriptRoot "..\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$outFile = Join-Path $backupDir "itsupport_$timestamp.sql"

if ($DatabaseUrl) {
    Write-Host "Sauvegarde depuis une base distante (DATABASE_URL fourni)..."
    docker run --rm postgres:16-alpine pg_dump --no-owner --clean --if-exists "$DatabaseUrl" | Out-File -Encoding utf8 $outFile
} else {
    Write-Host "Sauvegarde du conteneur Docker local 'itsupport_db'..."
    docker exec itsupport_db pg_dump -U itsupport --no-owner --clean --if-exists itsupport_db | Out-File -Encoding utf8 $outFile
}

if ($LASTEXITCODE -ne 0 -or -not (Test-Path $outFile) -or (Get-Item $outFile).Length -eq 0) {
    Write-Error "Échec de la sauvegarde — vérifiez que le conteneur tourne (docker ps) ou que DATABASE_URL est correcte."
    exit 1
}

Write-Host "Sauvegarde écrite : $outFile ($('{0:N0}' -f ((Get-Item $outFile).Length / 1KB)) Ko)"
