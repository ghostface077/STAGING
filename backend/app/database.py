"""
Configuration de la connexion à la base de données PostgreSQL via SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI fournissant une session de base de données par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
