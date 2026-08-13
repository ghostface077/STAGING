"""Gestion des équipes de support (réservée au Responsable IT et à l'Administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_manager, require_staff
from app.models.team import Team
from app.models.user import User
from app.schemas.common import Message
from app.schemas.team import TeamCreate, TeamOut, TeamUpdate

router = APIRouter(prefix="/api/teams", tags=["Équipes"])


def _base_query(db: Session):
    return db.query(Team).options(joinedload(Team.members))


@router.get("", response_model=list[TeamOut])
def list_teams(current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    return _base_query(db).order_by(Team.name).all()


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    team = _base_query(db).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipe introuvable.")
    return team


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    if db.query(Team).filter(Team.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette équipe existe déjà.")
    team = Team(name=payload.name, description=payload.description)
    if payload.member_ids:
        team.members = db.query(User).filter(User.id.in_(payload.member_ids)).all()
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.put("/{team_id}", response_model=TeamOut)
def update_team(team_id: int, payload: TeamUpdate, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipe introuvable.")
    data = payload.model_dump(exclude_unset=True)
    member_ids = data.pop("member_ids", None)
    for field, value in data.items():
        setattr(team, field, value)
    if member_ids is not None:
        team.members = db.query(User).filter(User.id.in_(member_ids)).all()
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}", response_model=Message)
def delete_team(team_id: int, current_user: User = Depends(require_manager), db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Équipe introuvable.")
    db.delete(team)
    db.commit()
    return Message(message="Équipe supprimée avec succès.")
