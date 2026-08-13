"""API des notifications utilisateur (cloche de notifications)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import Message
from app.schemas.notification import NotificationCountOut, NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).limit(100).all()


@router.get("/nombre-non-lues", response_model=NotificationCountOut)
def count_unread(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return NotificationCountOut(unread=count)


@router.post("/{notification_id}/lue", response_model=NotificationOut)
def mark_as_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification introuvable.")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/tout-marquer-lu", response_model=Message)
def mark_all_as_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read.is_(False)).update(
        {"is_read": True}
    )
    db.commit()
    return Message(message="Toutes les notifications ont été marquées comme lues.")
