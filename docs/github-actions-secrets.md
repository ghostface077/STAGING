# Secrets GitHub Actions requis

Configurés dans **Settings → Secrets and variables → Actions** sur le dépôt
GitHub. Les secrets utilisés par le déploiement doivent être créés dans les
environnements GitHub `staging` et `production` (ou au niveau du dépôt si les
deux environnements utilisent les mêmes valeurs).

Tant qu'un secret ci-dessous n'est pas défini, l'étape correspondante du
workflow (`.github/workflows/ci-cd.yml`) s'ignore avec un avertissement au
lieu d'échouer — les jobs `backend-tests`, `frontend-build` et `security`
tournent déjà sans aucun de ces secrets.

| Secret | Utilisé pour | Où le trouver |
|---|---|---|
| `SERVER_HOST` | Adresse IP ou nom DNS du serveur Ubuntu | Adresse publique du serveur |
| `SERVER_USER` | Compte Ubuntu utilisé pour le déploiement | Compte possédant Docker et `DEPLOY_PATH` |
| `DEPLOY_PATH` | Répertoire distant de l'application | Exemple : `/opt/it-support` |
| `SSH_PRIVATE_KEY` | Clé privée Ed25519 utilisée par GitHub Actions | Clé privée correspondant à une clé publique autorisée sur le serveur |
| `DEPLOY_ENV_FILE` | Contenu du fichier `.env.production` distant | Valeur de production complète, sans la publier dans le dépôt |
| `PROD_REPO_TOKEN` | Publication vers le dépôt de production | Jeton GitHub avec les droits nécessaires |

`PROD_REPOSITORY` est une variable GitHub Actions, par exemple
`ghostface077/STAGING` ou le dépôt de production réel.

Pour préparer le serveur, ajouter la clé publique correspondante dans
`/home/<SERVER_USER>/.ssh/authorized_keys`, puis vérifier ses permissions :

```sh
chmod 700 /home/<SERVER_USER>/.ssh
chmod 600 /home/<SERVER_USER>/.ssh/authorized_keys
chown -R <SERVER_USER>:<SERVER_USER> /home/<SERVER_USER>/.ssh
```

La valeur de `SSH_PRIVATE_KEY` doit inclure les lignes `-----BEGIN ... PRIVATE KEY-----`
et `-----END ... PRIVATE KEY-----`, sans guillemets. La clé doit être ajoutée
dans les deux environnements si les jobs staging et production sont protégés
par des secrets d'environnement distincts.

`GITHUB_TOKEN` (utilisé par l'étape gitleaks) est fourni automatiquement par
GitHub Actions — rien à configurer.

Aucun de ces secrets n'est nécessaire pour que les jobs de test/build/sécurité
fonctionnent : ils ne conditionnent que le job `deploy`, lui-même déjà
protégé par `needs: [backend-tests, frontend-build, security]`.
