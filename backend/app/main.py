"""
Point d'entrée de l'API FastAPI — IT Support (gestion de tickets).
"""
import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.database import get_db
from app.logging_config import configure_logging
from app.rate_limit import limiter
from app.security import ACCESS_TOKEN_COOKIE, decode_token

configure_logging()
logger = logging.getLogger("app.requests")
from app.routers import (
    attachments,
    audit_logs,
    auth,
    categories,
    comments,
    dashboard,
    departments,
    equipment,
    knowledge_base,
    notifications,
    priorities,
    reports,
    roles,
    satisfaction,
    slas,
    statuses,
    teams,
    tickets,
    users,
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute des en-têtes de sécurité standard à chaque réponse HTTP.

    `X-Content-Type-Options: nosniff` indique explicitement au navigateur de
    ne jamais tenter de deviner un type de contenu différent de celui déclaré
    dans `Content-Type` — en particulier utile pour le téléchargement des
    pièces jointes (correctif #05), en complément de `Content-Disposition:
    attachment` déjà systématiquement appliqué à cette réponse.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


def _extract_user_id(request: Request) -> str | None:
    """Best-effort, jamais levé : sert uniquement à enrichir un log, ne doit
    jamais interférer avec l'authentification réelle (gérée par
    `get_current_user`). Lit le cookie `access_token` (correctif #12 —
    auparavant l'en-tête Authorization, remplacé par un cookie httpOnly)."""
    token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        return None
    payload = decode_token(token)
    return str(payload["sub"]) if payload and "sub" in payload else None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Journalise chaque requête (correctif #10) : méthode, chemin, statut,
    durée, et l'utilisateur authentifié le cas échéant — jamais le corps de la
    requête, qui peut contenir un mot de passe ou un jeton."""

    async def dispatch(self, request: Request, call_next) -> Response:
        started_at = time.monotonic()
        response = await call_next(request)
        try:
            duration_ms = round((time.monotonic() - started_at) * 1000, 1)
            user_id = _extract_user_id(request)
            logger.info(
                "%s %s -> %s (%sms)%s",
                request.method, request.url.path, response.status_code, duration_ms,
                f" [user={user_id}]" if user_id else "",
            )
        except Exception:
            # Une erreur de journalisation ne doit jamais faire échouer la requête elle-même.
            pass
        return response


app = FastAPI(
    title="IT Support — API de gestion de tickets",
    description="API REST pour la plateforme de gestion des incidents et demandes informatiques.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (protection anti brute-force, correctif #04) : le limiteur est
# rattaché à l'état de l'application, et les dépassements de quota déclenchent
# le handler ci-dessous plutôt que la réponse par défaut de slowapi.
app.state.limiter = limiter


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Traduit les erreurs de validation Pydantic en un message générique en français."""
    logger.warning(
        "Validation invalide sur %s %s (%s champ(s) en erreur)",
        request.method, request.url.path, len(exc.errors()),
    )
    # jsonable_encoder est indispensable ici (pas un json.dumps direct) : les
    # erreurs levées par un validateur personnalisé (ValueError, ex. politique
    # de mot de passe du correctif #14) embarquent l'exception d'origine dans
    # `ctx`, non sérialisable telle quelle en JSON — bug latent depuis
    # l'écriture initiale de ce handler, resté invisible tant qu'aucun
    # validateur personnalisé n'existait dans le projet.
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({
            "message": "Les données envoyées sont invalides. Merci de vérifier le formulaire.",
            "details": exc.errors(),
        }),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Réponse générique en cas de dépassement du quota de requêtes : ne révèle
    ni le seuil configuré, ni la moindre information sur le compte visé."""
    logger.warning(
        "Quota de requêtes dépassé sur %s %s depuis %s",
        request.method, request.url.path, request.client.host if request.client else "IP inconnue",
    )
    response = JSONResponse(
        status_code=429,
        content={"message": "Trop de tentatives. Merci de réessayer dans quelques instants."},
    )
    return limiter._inject_headers(response, request.state.view_rate_limit)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Filet de sécurité pour toute exception non prévue (correctif #10) :
    journalise la trace complète côté serveur, sans jamais l'exposer au client.
    Starlette donne toujours priorité au gestionnaire le plus spécifique
    (HTTPException a le sien, déjà enregistré par FastAPI) : ce gestionnaire
    générique ne capte donc que les erreurs réellement non gérées (bugs,
    erreurs de base de données, etc.), jamais les 401/403/404 habituels."""
    logger.exception("Erreur non gérée sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"message": "Une erreur interne est survenue. Merci de réessayer plus tard."},
    )


@app.get("/api/health", tags=["Santé"])
def health_check():
    """Liveness : l'API FastAPI est démarrée et joignable. Ne touche jamais
    la base de données — c'est volontaire : c'est cet endpoint que Render
    (ou tout orchestrateur) doit utiliser pour décider de redémarrer le
    conteneur. Un Neon momentanément indisponible (mise en veille du palier
    gratuit, pic de latence) ne doit jamais provoquer un redémarrage inutile
    du backend, qui n'y changerait rien. Pour l'état réel de la base, voir
    /api/health/db."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/api/health/db", tags=["Santé"])
def health_check_db(db: Session = Depends(get_db)):
    """Readiness base de données : exécute un SELECT 1 en lecture seule pour
    confirmer que PostgreSQL/Neon répond réellement (pas seulement que
    l'URL est configurée). Indépendant de /api/health — voir sa docstring
    sur pourquoi ils ne doivent jamais être fusionnés. Ne renvoie jamais le
    détail de l'erreur ni DATABASE_URL au client : seul le statut booléen
    est exposé, le détail complet part dans les logs serveur (correctif #10,
    unhandled_exception_handler ci-dessous applique le même principe)."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except SQLAlchemyError:
        logger.exception("Échec du contrôle de disponibilité de la base de données (/api/health/db)")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "unreachable"},
        )


# Enregistrement de l'ensemble des routers de l'application
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(departments.router)
app.include_router(teams.router)
app.include_router(categories.router)
app.include_router(priorities.router)
app.include_router(statuses.router)
app.include_router(equipment.router)
app.include_router(slas.router)
app.include_router(tickets.router)
app.include_router(comments.router)
app.include_router(attachments.router)
app.include_router(satisfaction.router)
app.include_router(notifications.router)
app.include_router(knowledge_base.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(audit_logs.router)
