"""Configuration centralisée du logging applicatif (correctif #10).

Distinct de `audit_logs` (journal MÉTIER : qui a créé/modifié/supprimé quoi,
consultable par l'administrateur) — ce module configure le journal
OPÉRATIONNEL/SÉCURITÉ : échecs d'authentification, requêtes, erreurs serveur.
Sortie sur stdout/stderr, capturée par Docker comme flux de logs (aucun fichier
à gérer, aucune rotation à configurer côté application).
"""
import logging

from app.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging() -> None:
    """Configure le logger racine de l'application. Idempotent : peut être
    appelé plusieurs fois (tests, rechargement) sans dupliquer les handlers."""
    root_logger = logging.getLogger("app")
    root_logger.setLevel(settings.log_level.upper())

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(handler)

    # propagate reste à True (comportement par défaut) : le logger racine de
    # Python n'a par défaut aucun handler (uvicorn configure ses propres
    # loggers "uvicorn.*", jamais le root), donc la propagation ne produit
    # aucune sortie dupliquée — et elle est nécessaire pour que `caplog`
    # (qui écoute sur le logger racine) puisse capturer nos logs en tests.
