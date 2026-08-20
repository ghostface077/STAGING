# Sauvegarde et restauration — PostgreSQL

Ce guide couvre la base de données uniquement. Le plan de secours complet du
déploiement (rollback frontend/backend, échec de build...) est traité dans le
guide de déploiement (Groupe C/D).

## Pourquoi

`docker compose down` sans `-v` conserve les volumes (donc les données), mais
`docker compose down -v`, une réinstallation, ou un incident chez l'hébergeur
peuvent faire perdre les données. Une sauvegarde régulière est la seule
protection réelle contre ça.

## Sauvegarder

**Conteneur Docker local** (docker-compose.prod.yml en cours d'exécution) :
```powershell
.\scripts\backup-postgres.ps1
```

**Base distante (Neon, ou tout PostgreSQL accessible par URL)** :
```powershell
.\scripts\backup-postgres.ps1 -DatabaseUrl "postgresql://user:pass@host/db?sslmode=require"
```

Chaque exécution écrit un fichier horodaté dans `backups/` (ex.
`backups/itsupport_2026-08-20_12-00-00.sql`) — ce dossier est exclu de Git
(`.gitignore`) : une sauvegarde contient des données réelles, elle ne doit
jamais être commitée.

**Fréquence recommandée pour une démo** : une sauvegarde manuelle juste avant
la présentation (données dans l'état voulu), une autre juste après si les
données changent pendant la démo et méritent d'être conservées.

## Restaurer

⚠️ **Destructif** : la restauration écrase les données actuelles.

```powershell
.\scripts\restore-postgres.ps1 -BackupFile ".\backups\itsupport_2026-08-20_12-00-00.sql"
```

Le script demande une confirmation explicite (`OUI`) avant d'agir.

## Export ponctuel d'une table (sans passer par un fichier de sauvegarde complet)

Utile pour vérifier ou extraire une donnée précise sans tout restaurer :
```bash
docker exec itsupport_db psql -U itsupport -d itsupport_db -c "\copy (SELECT * FROM tickets) TO STDOUT WITH CSV HEADER" > tickets_export.csv
```

## En cas d'échec pendant la sauvegarde/restauration

| Symptôme | Cause probable | Action |
|---|---|---|
| `docker exec itsupport_db` échoue | Le conteneur ne tourne pas | `docker ps` pour vérifier, `docker compose -f docker-compose.prod.yml up -d db` pour le relancer |
| Fichier de sauvegarde vide (0 octet) | Mauvais identifiants, ou base vide | Vérifier `POSTGRES_USER`/`POSTGRES_DB` dans `.env.production` |
| `psql: FATAL: password authentication failed` (Neon) | URL de connexion expirée ou mot de passe changé | Régénérer l'URL de connexion depuis le tableau de bord Neon |
| Restauration : erreurs `relation already exists` | Normal et sans gravité — le dump est généré avec `--clean --if-exists`, ces erreurs apparaissent seulement si le script pg_dump utilisé pour la sauvegarde n'était pas celui de ce dépôt | Vérifier que la sauvegarde provient bien de `backup-postgres.ps1`/`.sh` |
