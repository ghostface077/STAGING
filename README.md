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
| `SECRET_KEY` | Clé secrète de signature des tokens JWT (**à changer en production**) |
| `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Paramètres du token JWT |
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

| Rôle | E-mail | Mot de passe |
|---|---|---|
| Administrateur | `admin@itsupport.example` | `Admin123!` |
| Responsable IT | `karim.benali@itsupport.example` | `Responsable123!` |
| Technicien | `fatou.ndiaye@itsupport.example` | `Technicien123!` |
| Technicien | `yacine.mansour@itsupport.example` | `Technicien123!` |
| Utilisateur | `lucas.moreau@itsupport.example` | `Utilisateur123!` |

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

## Sécurité

- Mots de passe hachés avec bcrypt (jamais stockés en clair).
- Authentification par token JWT signé, avec expiration.
- Contrôle d'accès par rôle (RBAC) appliqué côté backend sur chaque endpoint sensible (la protection frontend n'est qu'un confort d'interface).
- Validation stricte des données entrantes via Pydantic.
- Upload de fichiers contrôlé (extension, type MIME, taille maximale, nom de fichier généré aléatoirement).
- Journal d'audit (`audit_logs`) et historique de ticket (`ticket_history`) pour la traçabilité.
- CORS restreint à l'origine du frontend.
- Aucun secret dans le code source : tout passe par les variables d'environnement.

## Limites connues et pistes d'évolution

Par souci de transparence, voici ce qui est volontairement simplifié dans cette première version :

- **Export PDF/Excel** : seul l'export CSV est implémenté (`GET /api/reports/export.csv`) ; l'endpoint `/api/reports` est structuré pour accueillir des exporteurs PDF/Excel supplémentaires sans changement d'architecture.
- **Pagination des tickets** : la liste des tickets est paginée côté frontend (l'API retourne la liste complète filtrée). Une pagination `skip/limit` côté API serait recommandée avant un déploiement avec un très grand volume de tickets.
- **Sélecteur de date** : les champs de date utilisent le sélecteur natif du navigateur (`<input type="date">`) plutôt qu'un composant `Calendar` personnalisé.
- **Notifications temps réel** : la cloche de notifications se met à jour par sondage périodique (toutes les 30 secondes), pas par WebSocket.
- **Reconnexion administrateur/portail** : consulter `/admin/tickets` puis ouvrir un ticket redirige vers la page de détail du portail standard (`/tickets/{id}`), qui reste pleinement fonctionnelle mais sort visuellement du thème du back-office.
