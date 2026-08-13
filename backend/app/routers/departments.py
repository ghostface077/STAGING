"""Gestion des services / départements (réservée à l'administrateur)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin, require_staff
from app.models.department import Department
from app.models.user import User
from app.schemas.common import Message
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/departments", tags=["Services"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    return db.query(Department).order_by(Department.name).all()


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce service existe déjà.")
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: int, payload: DepartmentUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service introuvable.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    db.commit()
    db.refresh(department)
    return department


@router.delete("/{department_id}", response_model=Message)
def delete_department(department_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service introuvable.")
    db.delete(department)
    db.commit()
    return Message(message="Service supprimé avec succès.")
