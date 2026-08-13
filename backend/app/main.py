"""
Point d'entrée de l'API FastAPI — IT Support (gestion de tickets).
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
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

app = FastAPI(
    title="IT Support — API de gestion de tickets",
    description="API REST pour la plateforme de gestion des incidents et demandes informatiques.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Traduit les erreurs de validation Pydantic en un message générique en français."""
    return JSONResponse(
        status_code=422,
        content={
            "message": "Les données envoyées sont invalides. Merci de vérifier le formulaire.",
            "details": exc.errors(),
        },
    )


@app.get("/api/health", tags=["Santé"])
def health_check():
    """Vérifie que l'API est démarrée et joignable."""
    return {"status": "ok", "environment": settings.environment}


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
