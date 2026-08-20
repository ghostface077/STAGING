# Secrets GitHub Actions requis

Configurés dans **Settings → Secrets and variables → Actions → New repository
secret** sur https://github.com/jdmusca/it-support.

Tant qu'un secret ci-dessous n'est pas défini, l'étape correspondante du
workflow (`.github/workflows/ci-cd.yml`) s'ignore avec un avertissement au
lieu d'échouer — les jobs `backend-tests`, `frontend-build` et `security`
tournent déjà sans aucun de ces secrets.

| Secret | Utilisé pour | Où le trouver |
|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Déclenche un déploiement Render après succès des tests | Tableau de bord Render → service backend → **Settings → Deploy Hook** (voir guide de déploiement, Phase 5) |
| `PROD_DATABASE_URL` | Sauvegarde automatique de la base avant chaque déploiement | Tableau de bord Neon → **Connection string** (voir guide de déploiement, Phase 5) |

`GITHUB_TOKEN` (utilisé par l'étape gitleaks) est fourni automatiquement par
GitHub Actions — rien à configurer.

Aucun de ces secrets n'est nécessaire pour que les jobs de test/build/sécurité
fonctionnent : ils ne conditionnent que le job `deploy`, lui-même déjà
protégé par `needs: [backend-tests, frontend-build, security]`.
