"""Limiteur de débit global (protection anti brute-force). Défini dans son
propre module pour être importé à la fois par `main.py` (enregistrement du
handler d'exception) et par les routers qui appliquent une limite (ex. login),
sans dépendance circulaire.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Clé de limitation : l'adresse IP du client (comportement par défaut de slowapi).
# Stockage en mémoire du processus par défaut — suffisant pour une seule
# instance backend ; à faire évoluer vers un backend partagé (Redis) si
# l'application est un jour déployée derrière plusieurs instances.
limiter = Limiter(key_func=get_remote_address)
