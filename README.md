# IT Support — Plateforme de gestion de tickets

Application complète de gestion des incidents et demandes informatiques pour un service IT Support : création et suivi de tickets, attribution aux techniciens, SLA, base de connaissances, équipements, notifications, statistiques et back-office administrateur.

Toute l'interface, les données de démonstration, les messages et la documentation sont en **français**.

---

## Sommaire

- [Présentation](#présentation)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration et variables d'environnement](#configuration-et-variables-denvironnement)
- [Lancement avec Docker](#lancement-avec-docker)
- [Migrations PostgreSQL (Alembic)](#migrations-postgresql-alembic)
- [Données de démonstration (seed)](#données-de-démonstration-seed)
- [Comptes de démonstration](#comptes-de-démonstration)
- [Frontend](#frontend)
- [Backend](#backend)
- [API](#api)
- [Tests](#tests)
- [Structure du projet](#structure-du-projet)
- [Sécurité](#sécurité)
- [Limites connues et pistes d'évolution](#limites-connues-et-pistes-dévolution)

---

## Présentation

L'application couvre le cycle de vie complet d'un ticket :

```
Créer → Enregistrer → Attribuer → Prendre en charge → Traiter → Résoudre → Fermer → Évaluer
```

Quatre rôles sont gérés avec des permissions distinctes :

- **Utilisateur** — crée des tickets, suit leurs tickets, consulte la base de connaissances, évalue le support.
- **Technicien** — traite les tickets assignés ou disponibles, ajoute des solutions, escalade si besoin.
- **Responsable IT** — supervise les équipes, les SLA, les statistiques et les rapports.
- **Administrateur** — gère l'ensemble des données de référence (utilisateurs, rôles, catégories, SLA, etc.) depuis un back-office dédié.

## Architecture

Monorepo composé de deux applications communiquant via une API REST, orchestrées par Docker Compose :

```
it-support/
├── backend/          API FastAPI (Python) + SQLAlchemy + Alembic
├── frontend/          Application Next.js 14 (TypeScript, App Router)
├── docker-compose.yml
├── .env / .env.example
└── README.md
```

**Stack technique :**

| Couche | Technologies |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, TanStack Query, Tailwind CSS, Radix UI, Lucide React, React Hook Form, Zod, Recharts |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, JWT (python-jose), Passlib (bcrypt) |
| Base de données | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |

## Prérequis

- [Docker](https://www.docker.com/) et Docker Compose (méthode recommandée)
- Pour un développement en dehors de Docker : Python 3.12+, Node.js 20+, PostgreSQL 16

## Installation

```bash
git clone <url-du-dépôt>
cd it-support
cp .env.example .env
```

Modifiez `.env` si nécessaire (mots de passe, secrets JWT, etc. — voir section suivante).

## Configuration et variables d'environnement

Toutes les variables sont centralisées dans le fichier `.env` à la racine (voir `.env.example` pour la liste complète et les valeurs par défaut) :

| Variable | Rôle |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Identifiants de la base PostgreSQL |
| `DATABASE_URL` | Chaîne de connexion complète utilisée par le backend |
| `SECRET_KEY` | Clé secrète de signature des tokens JWT. **Obligatoire, sans valeur par défaut** : le backend refuse de démarrer si elle est absente, et refuse de démarrer en production (`ENVIRONMENT=production`) si elle correspond à une valeur de démonstration connue ou fait moins de 32 caractères. Générez-la avec `openssl rand -hex 32`. |
| `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Paramètres du token JWT |
| `SEED_ON_STARTUP` | Exécute automatiquement `python -m app.seed` (comptes de démonstration, dont l'administrateur par défaut) au démarrage du conteneur backend. **Doit être `false` en production** — le backend refuse de toute façon de démarrer en production si cette valeur reste à `true`. |
| `BACKEND_CORS_ORIGINS` | Origines autorisées par le CORS (le frontend) |
| `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB` | Répertoire et taille maximale des pièces jointes |
| `NEXT_PUBLIC_API_URL` | URL de l'API telle qu'appelée par le frontend |
| `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD` | Identifiants du compte administrateur créé par le seed |

⚠️ Ne jamais committer le fichier `.env` réel. `SECRET_KEY` et les mots de passe doivent être remplacés par des valeurs fortes avant tout déploiement.

## Lancement avec Docker

Depuis la racine du projet :

```bash
docker compose up --build
```

Cette commande :

1. démarre PostgreSQL et attend qu'il soit prêt (`healthcheck`) ;
2. construit et démarre le backend FastAPI, applique les migrations Alembic (`alembic upgrade head`), puis exécute le script de données de démonstration (`python -m app.seed`) ;
3. construit et démarre le frontend Next.js.

Une fois démarré :

- Frontend : http://localhost:3000
- API backend : http://localhost:8000/api
- Documentation interactive de l'API (Swagger) : http://localhost:8000/api/docs

Pour arrêter : `Ctrl+C` puis `docker compose down` (ajoutez `-v` pour supprimer aussi les volumes, y compris les données PostgreSQL).

> **Accès direct à PostgreSQL en local (psql, DBeaver...)** : le port 5432 n'est plus publié par défaut (voir section Sécurité). Créez un fichier `docker-compose.override.yml` à la racine (chargé automatiquement par `docker compose up`, non versionné) :
> ```yaml
> services:
>   db:
>     ports:
>       - "5432:5432"
> ```

## Migrations PostgreSQL (Alembic)

Les migrations sont exécutées automatiquement au démarrage du conteneur backend. Pour les piloter manuellement (backend lancé en local, hors Docker) :

```bash
cd backend
alembic upgrade head          # applique toutes les migrations
alembic downgrade -1          # annule la dernière migration
alembic revision --autogenerate -m "description"   # génère une nouvelle migration à partir des modèles
```

## Données de démonstration (seed)

Le script `backend/app/seed.py` est **idempotent** : il peut être exécuté plusieurs fois sans dupliquer les données. Il crée :

- les rôles, services, catégories/sous-catégories, priorités, statuts et SLA de référence ;
- 10 utilisateurs fictifs (administrateur, responsable IT, techniciens, utilisateurs) ;
- 2 équipes de support ;
- 6 équipements ;
- 6 tickets d'exemple à différents stades du cycle de vie, avec commentaires, historique et une évaluation de satisfaction ;
- 4 articles de base de connaissances.

Toutes les données sont fictives. Exécution manuelle :

```bash
docker compose exec backend python -m app.seed
```

## Comptes de démonstration

Le seed crée un compte par rôle (un Administrateur, un Responsable IT, trois Techniciens, cinq Utilisateurs — voir `app/seed.py`). Les e-mails sont fixes ; **les mots de passe ne sont pas publiés ici** et doivent être configurés dans votre fichier `.env` local (racine du projet), via les variables `SEED_ADMIN_PASSWORD`, `SEED_MANAGER_PASSWORD`, `SEED_TECHNICIAN_PASSWORD` et `SEED_USER_PASSWORD` (voir `.env.example`). Consultez votre `.env` pour retrouver les identifiants de connexion.

| Rôle | E-mail | Mot de passe |
|---|---|---|
| Administrateur | `admin@itsupport.example` | valeur de `SEED_ADMIN_PASSWORD` dans `.env` |
| Responsable IT | `karim.benali@itsupport.example` | valeur de `SEED_MANAGER_PASSWORD` dans `.env` |
| Technicien | `fatou.ndiaye@itsupport.example`, `yacine.mansour@itsupport.example`, `chloe.fontaine@itsupport.example` | valeur de `SEED_TECHNICIAN_PASSWORD` dans `.env` |
| Utilisateur | `lucas.moreau@itsupport.example` (et 4 autres, voir `app/seed.py`) | valeur de `SEED_USER_PASSWORD` dans `.env` |

Si une de ces variables est absente au moment du seed, un mot de passe aléatoire est généré automatiquement pour le(s) compte(s) concerné(s) — il n'est jamais journalisé ; définissez la variable si vous devez connaître ou fixer ce mot de passe.

Connexion standard : http://localhost:3000/login — Back-office administrateur : http://localhost:3000/admin/login

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # si lancé hors Docker
npm run dev
```

Structure des pages principales : `/login`, `/dashboard`, `/tickets`, `/tickets/nouveau`, `/tickets/[id]`, `/mes-tickets`, `/tickets/non-assignes`, `/notifications`, `/knowledge-base`, `/equipment`, `/profil`, `/teams`, `/technicians`, `/slas`, `/reports`, ainsi que l'ensemble du back-office sous `/admin/*`.

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows — sous Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## API

L'API REST est entièrement documentée et testable via Swagger UI (`/api/docs`) et ReDoc (`/api/redoc`) une fois le backend démarré. Principaux groupes d'endpoints :

- `POST /api/auth/login`, `/register`, `GET /api/auth/me`, `POST /api/auth/logout`
- `GET|POST|PUT|DELETE /api/tickets`, actions `POST /api/tickets/{id}/{assign|status|priority|resolve|close|reopen|escalate}`
- `GET|POST /api/tickets/{id}/comments`, `PUT|DELETE /api/comments/{id}`
- `POST /api/tickets/{id}/attachments`, `GET /api/attachments/{id}/download`
- `GET|POST|PUT|DELETE /api/users`, `/roles`, `/departments`, `/teams`, `/categories`, `/priorities`, `/statuses`, `/slas`, `/equipment`
- `GET /api/dashboard/statistics|tickets-by-status|tickets-by-priority|tickets-by-category|tickets-by-technician|sla`
- `GET /api/reports/summary`, `GET /api/reports/export.csv`
- `GET /api/audit-logs`

## Tests

**Backend** (pytest, base SQLite isolée en mémoire — aucune dépendance à PostgreSQL) :

```bash
cd backend
pip install -r requirements.txt
pytest
```

Couvre : authentification, création/attribution/résolution de tickets, permissions par rôle, visibilité des notes internes, calcul du respect des SLA.

**Frontend** : l'application est validée par une compilation stricte (`npm run build`, TypeScript strict + ESLint) qui garantit l'absence d'erreur de typage ou de rendu. Les flux critiques (connexion, création de ticket, changement de statut, navigation) sont couverts manuellement via les scénarios de démonstration ci-dessus ; l'ajout de tests end-to-end (Playwright/Cypress) est documenté comme piste d'évolution.

## Structure du projet

```
backend/
├── app/
│   ├── models/        Modèles SQLAlchemy (18 tables)
│   ├── schemas/        Schémas Pydantic (validation des entrées/sorties)
│   ├── routers/         Endpoints FastAPI par domaine métier
│   ├── services/         Logique métier (référence de ticket, SLA, notifications, historique)
│   ├── utils/            Utilitaires (upload de fichiers sécurisé)
│   ├── config.py, database.py, security.py, deps.py, main.py
│   └── seed.py
├── alembic/               Migrations de base de données
├── tests/                  Tests backend (pytest)
└── uploads/                 Pièces jointes (volume Docker)

frontend/
├── app/
│   ├── (portal)/            Espace applicatif principal (utilisateur/technicien/responsable)
│   └── admin/                Back-office administrateur
├── components/
│   ├── ui/                    Composants shadcn/ui (Button, Card, Table, Dialog, etc.)
│   ├── layout/                Sidebar, topbar, notifications, menu utilisateur
│   ├── tickets/                Composants métier tickets (badges, SLA, commentaires, actions)
│   ├── dashboard/              Graphiques (Recharts)
│   └── common/                 Composants génériques réutilisables
├── hooks/                     Hooks TanStack Query pour les données de référence
└── lib/                        Client API, contexte d'authentification, types, constantes
```

## Déploiement en production

Documentation complète dans `docs/` :
- [`docs/deploiement-vercel-render-neon.md`](docs/deploiement-vercel-render-neon.md) — guide pas-à-pas (Vercel + Render + Neon, paliers gratuits)
- [`docs/checklist-validation.md`](docs/checklist-validation.md) — checklist post-déploiement
- [`docs/guide-demonstration.md`](docs/guide-demonstration.md) — préparer une démonstration
- [`docs/sauvegarde-restauration.md`](docs/sauvegarde-restauration.md) — sauvegarde/restauration PostgreSQL
- [`docs/plan-de-secours.md`](docs/plan-de-secours.md) — rollback et procédures d'échec
- [`docs/github-actions-secrets.md`](docs/github-actions-secrets.md) — secrets requis par `.github/workflows/ci-cd.yml`

Déploiement local avec Docker : `docker-compose.prod.yml` (voir son en-tête pour l'usage), variables dans `.env.production` (gabarit : `.env.production.example`).

## Sécurité

- Mots de passe hachés avec bcrypt (jamais stockés en clair).
- Authentification par token JWT signé, avec expiration.
- Contrôle d'accès par rôle (RBAC) appliqué côté backend sur chaque endpoint sensible (la protection frontend n'est qu'un confort d'interface).
- Validation stricte des données entrantes via Pydantic.
- Upload de fichiers contrôlé (extension, type MIME, taille maximale, nom de fichier généré aléatoirement).
- Journal d'audit (`audit_logs`) et historique de ticket (`ticket_history`) pour la traçabilité.
- CORS restreint à l'origine du frontend.
- Aucun secret dans le code source : tout passe par les variables d'environnement (`.env`, jamais committé — voir `.gitignore`).
- **`SECRET_KEY` obligatoire, sans valeur par défaut** : le backend refuse de démarrer si elle est absente, et refuse de démarrer en production si elle correspond à une valeur de démonstration connue ou fait moins de 32 caractères (`app/config.py`).
- **Seed de démonstration désactivable** : `SEED_ON_STARTUP=false` empêche la création automatique des comptes de démonstration (dont l'administrateur par défaut) — obligatoire en production, sous peine d'échec de démarrage volontaire.
- **PostgreSQL non exposé publiquement** : le port 5432 n'est plus publié par `docker-compose.yml` (base accessible uniquement depuis le réseau Docker interne). L'accès local de développement passe par un `docker-compose.override.yml` non versionné (voir section Docker ci-dessus).
- Si un compte administrateur de démonstration est malgré tout créé (environnement de développement), changez son mot de passe dès la première connexion réelle.

## Limites connues et pistes d'évolution

Par souci de transparence, voici ce qui est volontairement simplifié dans cette première version :

- **Export Excel natif** : CSV (`GET /api/reports/export.csv`) et PDF (`GET /api/reports/export.pdf`, synthèse chiffrée + liste des tickets) sont implémentés et partagent leur calcul de données (`_compute_summary`/`_ticket_rows`) ; un export `.xlsx` natif pourrait être ajouté en réutilisant les mêmes fonctions.
- **Pagination des tickets** : pagination réelle côté API (`page`/`page_size`, réponse `Page[T]`), appliquée à `GET /api/tickets`.
- **Sélecteur de date** : les champs de date utilisent le sélecteur natif du navigateur (`<input type="date">`) plutôt qu'un composant `Calendar` personnalisé.
- **Notifications temps réel** : la cloche de notifications se met à jour par sondage périodique (toutes les 30 secondes), pas par WebSocket.
- **Reconnexion administrateur/portail** : consulter `/admin/tickets` puis ouvrir un ticket redirige vers la page de détail du portail standard (`/tickets/{id}`), qui reste pleinement fonctionnelle mais sort visuellement du thème du back-office.
