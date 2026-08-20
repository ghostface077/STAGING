# Plan de secours

Pour la base de données spécifiquement (sauvegarde/restauration), voir
`docs/sauvegarde-restauration.md`. Ce document couvre le reste : que faire
si un déploiement échoue ou si un service tombe, y compris juste avant ou
pendant une démonstration.

## Le déploiement Render échoue (build ou démarrage)

1. Render → service backend → onglet **Logs** : la cause est presque
   toujours visible directement (erreur de migration Alembic, variable
   d'environnement manquante, erreur de connexion à Neon).
2. **Rollback immédiat** : onglet **Deploys** → trouver le dernier déploiement marqué « Live » avant l'échec → **Redeploy**. Render relance cette version précédente sans reconstruire — l'application redevient disponible en quelques dizaines de secondes.
3. Corriger la cause en local, valider (`npm run build` / `pytest`), commiter, repousser — le déploiement automatique reprendra.

## Le déploiement Vercel échoue

1. Vercel garde **chaque déploiement précédent**, même après un échec.
2. Onglet **Deployments** → trouver le dernier déploiement réussi → menu **⋯** → **Promote to Production**. Bascule instantané, aucune reconstruction.

## Neon (base de données) inaccessible ou corrompue

1. Vérifier d'abord que ce n'est pas juste une mise en veille (palier gratuit) : une requête déclenche normalement un réveil automatique en quelques secondes.
2. Si les données sont réellement corrompues ou perdues : restaurer depuis la dernière sauvegarde (`docs/sauvegarde-restauration.md`).
3. Neon conserve un historique de points de restauration selon le palier — vérifier **Restore** dans le tableau de bord Neon avant de recourir à une sauvegarde manuelle : ça peut être plus récent.

## Échec total le jour de la démonstration (plan B)

Si Vercel/Render/Neon sont indisponibles au mauvais moment (panne côté
hébergeur, quota gratuit épuisé...), l'environnement local déjà utilisé tout
au long de ce projet reste un filet de secours fonctionnel et déjà éprouvé :

```powershell
cd C:\Users\HP\it-support\backend
PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cd C:\Users\HP\it-support\frontend
npm run dev
```

Démonstration alors en local (`http://localhost:3000`) sur la machine
elle-même, sans dépendre d'aucun service externe — moins impressionnant
qu'une URL publique, mais garanti de fonctionner.

## Contact / historique

En cas de doute sur l'état d'un déploiement, `git log --oneline` et l'onglet
**Deploys** de Render/Vercel donnent toujours l'état réel — ne jamais
supposer qu'un déploiement a réussi sans le vérifier dans ces interfaces.
