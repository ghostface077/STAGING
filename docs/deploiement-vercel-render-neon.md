# Guide de déploiement — Vercel + Render + Neon (gratuit)

Architecture retenue pour minimiser les coûts : trois services gratuits
distincts, chacun spécialisé dans sa couche.

```
Navigateur → Vercel (frontend Next.js) → Render (backend FastAPI) → Neon (PostgreSQL)
```

**À savoir avant de commencer** : les paliers gratuits de Render et Neon
mettent le service en veille après une période d'inactivité. Le premier
appel après une veille prend 20 à 60 secondes de plus (temps de réveil). Ce
n'est pas un bug — voir la section « Avant une démonstration » à la fin.

Suivre les étapes **dans cet ordre** : chaque service a besoin d'une
information produite par le précédent.

---

## Étape 1 — Neon (PostgreSQL)

1. Créer un compte sur https://neon.tech (connexion possible avec le compte GitHub `jdmusca`).
2. **New Project** → nom : `it-support` → version PostgreSQL : **16** → région : la plus proche de celle que vous choisirez pour Render à l'étape 2 (ex. toutes les deux en Europe, ou toutes les deux aux USA — réduit la latence entre le backend et la base).
3. Une fois créé, Neon affiche une **chaîne de connexion**, du type :
   ```
   postgresql://itsupport_owner:AbCdEf123456@ep-xxxx.eu-central-1.aws.neon.tech/it-support?sslmode=require
   ```
4. **Adaptez-la avant de vous en servir** : ce projet utilise le pilote `psycopg2`, il faut donc changer le préfixe :
   ```
   postgresql+psycopg2://itsupport_owner:AbCdEf123456@ep-xxxx.eu-central-1.aws.neon.tech/it-support?sslmode=require
   ```
   → C'est cette URL (avec `+psycopg2`) qui devient votre `DATABASE_URL`. Gardez-la de côté, elle sert aux étapes 2 et 6.

---

## Étape 2 — Render (backend FastAPI)

1. Créer un compte sur https://render.com (connexion avec GitHub, autoriser l'accès à `jdmusca/it-support`).
2. **New +** → **Web Service** → sélectionner le dépôt `it-support`.
3. Configuration du service :
   | Champ | Valeur |
   |---|---|
   | Name | `it-support-backend` |
   | Region | Celle choisie à l'étape 1 |
   | Root Directory | `backend` |
   | Runtime | **Docker** |
   | Dockerfile Path | `Dockerfile` (relatif au Root Directory ci-dessus, donc `backend/Dockerfile`) |
   | Instance Type | **Free** |
4. **Environment Variables** — ajouter (Add Environment Variable), une par ligne, valeurs tirées de `.env.production.example` :

   | Clé | Valeur |
   |---|---|
   | `DATABASE_URL` | La chaîne Neon **avec `+psycopg2`** de l'étape 1 |
   | `SECRET_KEY` | Générée localement avec `openssl rand -hex 32` (dans un terminal Git Bash) |
   | `ALGORITHM` | `HS256` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
   | `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |
   | `ENVIRONMENT` | `production` |
   | `SEED_ON_STARTUP` | `false` |
   | `UPLOAD_DIR` | `/app/uploads` |
   | `MAX_UPLOAD_SIZE_MB` | `15` |
   | `BACKEND_CORS_ORIGINS` | `http://localhost:3000` **provisoirement** — sera remplacé à l'étape 4 par l'URL Vercel réelle |

5. **Create Web Service**. Render construit l'image (`backend/Dockerfile`, qui applique automatiquement les migrations Alembic au démarrage via `docker-entrypoint.sh`) puis démarre le service.
6. Une fois « Live », notez l'URL fournie par Render, par ex. :
   ```
   https://it-support-backend.onrender.com
   ```
   Vérifiez qu'elle répond : ouvrez `https://it-support-backend.onrender.com/api/health` dans un navigateur → doit afficher `{"status":"ok"}` (ou équivalent).
7. **Settings → Deploy Hook** : copiez l'URL affichée — c'est la valeur du secret GitHub `RENDER_DEPLOY_HOOK_URL` (voir `docs/github-actions-secrets.md`).

---

## Étape 3 — Vercel (frontend Next.js)

1. Créer un compte sur https://vercel.com (connexion avec GitHub).
2. **Add New** → **Project** → importer `jdmusca/it-support`.
3. Configuration :
   | Champ | Valeur |
   |---|---|
   | Root Directory | `frontend` (cliquer **Edit** à côté de Root Directory pour le définir — indispensable dans un dépôt monorepo) |
   | Framework Preset | **Next.js** (détecté automatiquement une fois le Root Directory correct) |
   | Build Command | par défaut (`next build`) |
   | Output Directory | par défaut |
4. **Environment Variables** :
   | Clé | Valeur |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | `https://it-support-backend.onrender.com/api` (URL Render de l'étape 2, **avec `/api` à la fin**) |
5. **Deploy**. Une fois terminé, Vercel donne une URL, par ex. :
   ```
   https://it-support-jdmusca.vercel.app
   ```

---

## Étape 4 — Reconnecter le backend au frontend (CORS)

Le backend a été déployé avant de connaître l'URL Vercel définitive — il faut la lui donner maintenant :

1. Retour sur Render → service `it-support-backend` → **Environment**.
2. Modifier `BACKEND_CORS_ORIGINS` → mettre l'URL Vercel exacte de l'étape 3, **sans `/` final** :
   ```
   https://it-support-jdmusca.vercel.app
   ```
   (Plusieurs origines séparées par une virgule sont acceptées si vous avez aussi un domaine de prévisualisation Vercel à autoriser.)
3. **Save Changes** → Render redéploie automatiquement le service avec la nouvelle valeur.

---

## Étape 5 — Secrets GitHub (pour le déploiement automatisé)

Avec les URLs obtenues ci-dessus, complétez maintenant `docs/github-actions-secrets.md` :
- `RENDER_DEPLOY_HOOK_URL` = valeur copiée à l'étape 2.7
- `PROD_DATABASE_URL` = la même chaîne Neon (`+psycopg2`) que `DATABASE_URL`

À ajouter sur https://github.com/jdmusca/it-support/settings/secrets/actions.

---

## Étape 6 — Vérification de bout en bout

1. Ouvrir l'URL Vercel dans un navigateur.
2. Se connecter avec un compte créé manuellement (voir guide de démonstration — le seed automatique est désactivé en production, `SEED_ON_STARTUP=false`).
3. Créer un ticket de test, vérifier qu'il apparaît bien — confirme que Vercel → Render → Neon fonctionnent ensemble.

Si une étape échoue, voir la checklist de validation (Groupe D) et la section « Plan de secours » de `docs/sauvegarde-restauration.md`.

---

## Avant une démonstration

Render (free) et Neon (free) se mettent en veille après inactivité. **10 à 15 minutes avant** de présenter l'application à votre responsable :
1. Ouvrez l'URL Vercel et connectez-vous une fois — ça réveille Render, qui réveille Neon en interrogeant la base.
2. Naviguez sur 2-3 pages (tableau de bord, tickets) pour confirmer que tout répond normalement avant de commencer réellement la démonstration.
