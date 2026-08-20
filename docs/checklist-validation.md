# Checklist de validation post-déploiement

À dérouler une fois après le premier déploiement complet (Vercel + Render +
Neon connectés), puis avant chaque démonstration importante. Chaque ligne
correspond à une fonctionnalité réellement présente dans l'application (pas
une checklist générique) — cocher au fur et à mesure.

## Frontend

- [ ] `https://<votre-app>.vercel.app/login` charge sans erreur de compilation ni écran blanc
- [ ] Connexion avec un compte de démonstration (voir `guide-demonstration.md`) → redirection vers `/dashboard`
- [ ] Sidebar : les sections affichées correspondent au rôle connecté (ex. un compte Utilisateur ne voit pas « Rapports », « SLA », « Techniciens »)
- [ ] Navigation entre Tableau de bord, Tickets, Base de connaissances, Notifications sans rechargement complet
- [ ] Réactif : redimensionner la fenêtre (ou outils de dev, mode mobile) — sidebar se transforme en menu, tableaux ne débordent pas horizontalement de la page

## Backend / API

- [ ] `https://<votre-backend>.onrender.com/api/health` répond 200
- [ ] `https://<votre-backend>.onrender.com/api/docs` affiche la documentation Swagger (confirme que FastAPI tourne correctement)
- [ ] Connexion échouée (mauvais mot de passe) → message d'erreur clair, pas de 500
- [ ] Un compte **Utilisateur** qui appelle `/api/tickets` ne reçoit que ses propres tickets (jamais ceux des autres — vérifié dans l'onglet réseau du navigateur pendant que ce compte est connecté)
- [ ] Un compte **Technicien** ne voit dans sa liste par défaut que les tickets qui lui sont assignés

## Base de données (Neon)

- [ ] Le tableau de bord Neon indique le projet actif (pas suspendu de façon permanente)
- [ ] Écriture : créer un ticket depuis l'interface → réapparaît après un rafraîchissement de page (confirme la persistance réelle, pas un état local)
- [ ] Lecture : le tableau de bord (KPI, graphiques) reflète les tickets réellement présents en base

## Fonctionnalités métier

- [ ] **Création de ticket** : un compte Utilisateur crée un ticket avec pièce jointe → apparaît dans « Mes tickets »
- [ ] **Attribution** : un compte Technicien s'auto-assigne un ticket depuis « Non assignés » (bouton « Prendre en charge ») → le ticket quitte la liste des non-assignés
- [ ] **Résolution** : le Technicien assigné résout le ticket (action dédiée « Résoudre », pas un simple changement de statut) → statut passe à Résolu, la solution saisie s'affiche
- [ ] **Fermeture** : le demandeur (ou un Responsable IT/Administrateur) ferme le ticket résolu
- [ ] **Rapports** : un compte Responsable IT ou Administrateur génère un export depuis `/reports`
- [ ] **Administration** : un compte Administrateur crée un nouvel utilisateur depuis `/admin/users` et modifie une catégorie depuis `/admin/categories`

## Sécurité (rapide, pas un audit complet)

- [ ] Se déconnecter puis tenter d'accéder directement à `/dashboard` par l'URL → redirection vers `/login` (pas de contenu affiché)
- [ ] `BACKEND_CORS_ORIGINS` sur Render contient bien l'URL Vercel exacte (sinon les appels API échouent silencieusement en erreur CORS — visible dans la console du navigateur)
