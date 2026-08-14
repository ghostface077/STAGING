"""Machine à états du cycle de vie d'un ticket (correctif #13).

`change_status` (transition libre, réservée au personnel support) ne gère que
les statuts « actifs » — Résolu, Fermé et Réouvert restent exclusivement
accessibles via leurs endpoints dédiés (`resolve`/`close`/`reopen`), qui sont
les seuls à synchroniser correctement `resolved_at`/`closed_at`. Ce choix
élimine par construction l'incohérence qui existait quand `change_status`
pouvait faire sortir un ticket de Résolu/Fermé sans jamais réinitialiser ces
colonnes (le statut redevenait actif tout en gardant une date de résolution
non nulle, faussant les statistiques de temps de résolution)."""
from app.models.status import (
    STATUS_ANNULE,
    STATUS_EN_ATTENTE,
    STATUS_EN_COURS,
    STATUS_FERME,
    STATUS_NOUVEAU,
    STATUS_OUVERT,
    STATUS_REOUVERT,
    STATUS_RESOLU,
)

# Résolu et Fermé ne sont jamais atteints ni quittés via change_status :
# uniquement via resolve/close (entrée) et reopen (sortie).
MANAGED_ELSEWHERE_STATUSES = {STATUS_RESOLU, STATUS_FERME}

# Transitions autorisées via change_status, entre statuts actifs uniquement.
# Annulé est terminal : aucune transition sortante.
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    STATUS_NOUVEAU: {STATUS_OUVERT, STATUS_EN_COURS, STATUS_EN_ATTENTE, STATUS_ANNULE},
    STATUS_OUVERT: {STATUS_EN_COURS, STATUS_EN_ATTENTE, STATUS_ANNULE},
    STATUS_EN_COURS: {STATUS_EN_ATTENTE, STATUS_OUVERT, STATUS_ANNULE},
    STATUS_EN_ATTENTE: {STATUS_EN_COURS, STATUS_OUVERT, STATUS_ANNULE},
    STATUS_REOUVERT: {STATUS_EN_COURS, STATUS_EN_ATTENTE, STATUS_OUVERT, STATUS_ANNULE},
    STATUS_ANNULE: set(),
}


def describe_invalid_transition(*, current_status_name: str, target_status_name: str) -> str | None:
    """Retourne `None` si la transition est autorisée, sinon un message
    d'erreur explicite (en français, exploitable tel quel dans une réponse
    HTTP) expliquant pourquoi elle ne l'est pas."""
    if current_status_name == target_status_name:
        return "Le ticket est déjà à ce statut."

    if target_status_name in MANAGED_ELSEWHERE_STATUSES:
        action = "Résoudre" if target_status_name == STATUS_RESOLU else "Fermer"
        return f"Utilisez l'action « {action} » dédiée pour passer un ticket à ce statut."

    if current_status_name in MANAGED_ELSEWHERE_STATUSES:
        return f"Ce ticket est {current_status_name.lower()} : utilisez l'action « Réouvrir » pour le remettre en circulation."

    if target_status_name not in ALLOWED_STATUS_TRANSITIONS.get(current_status_name, set()):
        return f"Transition de « {current_status_name} » vers « {target_status_name} » non autorisée."

    return None
