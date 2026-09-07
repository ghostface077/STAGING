# CI/CD avec GitHub Actions et Docker Compose

Le parcours est :

```text
push sur staging -> CI/CD -> staging -> approbation -> production
```

GitHub Actions exécute les tests, construit les images et déploie par SSH sur
Ubuntu avec Docker Compose. Les données restent dans les volumes Docker.

## 1. Préparer chaque serveur Ubuntu

À faire sur le serveur staging et, séparément, sur le serveur production :

```bash
sudo apt update
sudo apt install -y ca-certificates curl openssh-server
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
mkdir -p /opt/it-support
```

Déconnectez-vous puis reconnectez-vous, puis vérifiez :

```bash
docker --version
docker compose version
```

Ouvrez les ports SSH `22` et HTTP `80`. Les ports applicatifs `3000` et
`8000` sont utilisés par Compose ; l'accès public recommandé passe par Nginx
sur le port `80`.

## 2. Créer la clé de déploiement

Sur votre ordinateur :

```bash
ssh-keygen -t ed25519 -C "github-actions-it-support" -f ~/.ssh/it-support-actions
```

Ajoutez `~/.ssh/it-support-actions.pub` dans `~/.ssh/authorized_keys` de
l'utilisateur Ubuntu. La clé privée sera uniquement enregistrée dans GitHub.

## 3. Configurer GitHub

Dans GitHub : `Settings` -> `Environments`, créez `staging` et `production`.
Dans chaque environnement, ajoutez ces secrets :

| Secret | Valeur |
|---|---|
| `SERVER_HOST` | IP ou nom DNS du serveur Ubuntu |
| `SERVER_USER` | utilisateur Ubuntu appartenant au groupe `docker` |
| `SSH_PRIVATE_KEY` | clé privée Ed25519 complète |
| `DEPLOY_PATH` | `/opt/it-support` |
| `DEPLOY_ENV_FILE` | contenu complet de l'environnement cible |

Dans `production`, activez `Required reviewers`. La production nécessitera
ainsi une approbation après le déploiement réussi sur staging.

Le secret `DEPLOY_ENV_FILE` doit contenir notamment :

```dotenv
POSTGRES_USER=itsupport
POSTGRES_PASSWORD=un_mot_de_passe_long_et_unique
POSTGRES_DB=itsupport_db
DATABASE_URL=postgresql+psycopg2://itsupport:un_mot_de_passe_long_et_unique@db:5432/itsupport_db
SECRET_KEY=une_cle_generee_avec_openssl_rand_hex_32
ENVIRONMENT=production
SEED_ON_STARTUP=false
BACKEND_PORT=8000
FRONTEND_PORT=3000
BACKEND_CORS_ORIGINS=https://votre-domaine.example
NEXT_PUBLIC_API_URL=/api
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=15
```

Générez `SECRET_KEY` avec `openssl rand -hex 32`. N'utilisez jamais les
valeurs de `.env.example` en production.

## 4. Déployer staging

Depuis le poste local :

```bash
git checkout -b staging
git push -u origin staging
```

Le workflow lance les tests backend, le contrôle TypeScript, le build
frontend, l'audit des dépendances et le build Docker Compose. S'ils réussissent,
il déploie staging.

Testez ensuite :

```text
http://IP_DU_SERVEUR_STAGING/
http://IP_DU_SERVEUR_STAGING/api/health
```

Diagnostic sur le serveur :

```bash
cd /opt/it-support
docker compose -f docker-compose.prod.yml --env-file .env.production ps
docker compose -f docker-compose.prod.yml --env-file .env.production logs --tail=100
```

## 5. Promouvoir en production

1. Poussez votre code sur la branche `staging`.
2. Attendez la réussite des tests, audits, builds et du déploiement staging.
3. Ouvrez le workflow GitHub Actions en attente sur l'environnement
	`production`.
4. Cliquez sur `Review deployments`, sélectionnez `production`, puis validez.

Le même commit sera alors déployé sur le serveur de production. Une Pull
Request vers `master` reste recommandée pour conserver un historique propre,
mais elle n'est plus nécessaire pour déclencher ce parcours.

## 6. Retour arrière

Pour revenir à une version précédente, créez une branche depuis le commit
voulu, vérifiez-la sur staging puis promouvez-la normalement vers `master`.
La commande `up -d --build` ne supprime pas les volumes PostgreSQL ni les
uploads.