# Restaure une sauvegarde .sql (produite par backup-postgres.ps1) dans le
# conteneur Docker local 'itsupport_db'. DESTRUCTIF : écrase les données
# actuelles de la base (le dump est généré avec --clean --if-exists).
#
# Usage :
#   .\scripts\restore-postgres.ps1 -BackupFile ".\backups\itsupport_2026-08-20_12-00-00.sql"

param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "Fichier de sauvegarde introuvable : $BackupFile"
    exit 1
}

Write-Host "⚠️  Ceci va ÉCRASER les données actuelles de la base 'itsupport_db'." -ForegroundColor Yellow
$confirm = Read-Host "Taper OUI en majuscules pour confirmer"
if ($confirm -ne "OUI") {
    Write-Host "Annulé."
    exit 0
}

Get-Content $BackupFile | docker exec -i itsupport_db psql -U itsupport -d itsupport_db

if ($LASTEXITCODE -ne 0) {
    Write-Error "La restauration a échoué — vérifiez le contenu du fichier et que le conteneur tourne."
    exit 1
}

Write-Host "Restauration terminée depuis : $BackupFile"
