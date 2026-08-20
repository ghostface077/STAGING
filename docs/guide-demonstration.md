# Préparer la démonstration

`SEED_ON_STARTUP=false` est **volontairement** forcé en production (voir
`app/config.py`) : l'application ne crée jamais de comptes de démonstration
toute seule sur un déploiement public. Il faut les créer une fois,
manuellement, avec des mots de passe qui n'ont jamais été utilisés ailleurs.

⚠️ **Ne réutilisez pas les mots de passe de démo vus dans cette conversation
ou dans un `.env` de développement local** (`Admin123!` et compagnie) — ils
ont circulé dans un historique de chat, ce n'est pas approprié pour un
déploiement accessible publiquement. Générez des valeurs propres, uniquement
pour cette démonstration.

## 1. Créer les comptes (une seule fois)

**Méthode retenue : seed temporaire avec des mots de passe dédiés.**

1. Sur Render → service backend → **Environment**, ajouter temporairement :
   | Clé | Valeur |
   |---|---|
   | `SEED_ON_STARTUP` | `true` |
   | `SEED_ADMIN_EMAIL` | votre choix, ex. `demo.admin@it-support.local` |
   | `SEED_ADMIN_PASSWORD` | un mot de passe fort, propre à cette démo |
   | `SEED_MANAGER_PASSWORD` | idem |
   | `SEED_TECHNICIAN_PASSWORD` | idem |
   | `SEED_USER_PASSWORD` | idem |
2. **Save Changes** → Render redéploie. Le seed s'exécute une fois au démarrage : 1 administrateur, 1 responsable IT, 3 techniciens, 5 utilisateurs, quelques tickets/équipements d'exemple (voir `backend/app/seed.py` pour le détail exact des comptes créés).
3. Vérifier que la connexion fonctionne avec le compte administrateur.
4. **Remettre immédiatement `SEED_ON_STARTUP` à `false`** et enlever les 4 variables `SEED_*_PASSWORD` de Render (elles ne doivent pas rester en clair dans les variables d'environnement une fois leur usage terminé). **Save Changes** → nouveau redéploiement, cette fois sans seed.

Notez les identifiants créés dans un gestionnaire de mots de passe — ils ne
sont plus régénérables sans relancer un seed (qui échouerait de toute façon
sur des comptes déjà existants).

## 2. Données réalistes pour la démonstration

Le seed crée déjà un jeu de données de base (tickets à différents statuts,
priorités, une équipe). Pour une démonstration plus vivante, créez en plus
**pendant que vous êtes connecté** :

- 2-3 tickets supplémentaires avec des titres concrets et représentatifs de vrais cas (« Imprimante service comptabilité hors ligne », « Demande d'accès VPN »)
- Un ticket déjà résolu avec une note de satisfaction, pour montrer cet aspect
- Un ticket en retard de SLA (priorité Critique, créé il y a plusieurs heures sans prise en charge) pour montrer la jauge SLA en état « Dépassé »

## 3. Déroulé suggéré pour la démonstration

1. Se connecter en **Administrateur** → tableau de bord global, KPI animés
2. Montrer le **Kanban** des tickets (glisser-déposer un ticket entre colonnes)
3. Ouvrir un ticket → jauge SLA circulaire, timeline, commentaires
4. Se déconnecter, se reconnecter en **Technicien** → montrer que la vue est différente (seulement ses tickets assignés + file « Non assignés »), prendre en charge un ticket
5. Se reconnecter en **Utilisateur** → créer un nouveau ticket, montrer qu'il ne voit que les siens
6. Revenir en Administrateur → back-office (`/admin`), base de connaissances

## 4. Avant de commencer réellement

Voir la fin de `deploiement-vercel-render-neon.md` — réveiller Render/Neon
10-15 minutes avant, et dérouler `checklist-validation.md` une dernière fois.
