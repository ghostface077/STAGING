from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RefreshToken(Base):
    """Session de rafraîchissement (correctif #12) : une ligne par refresh token
    émis. Le JWT lui-même reste sans état, mais sa validité réelle dépend de
    cette table — c'est ce qui rend une déconnexion, un changement de mot de
    passe ou une désactivation de compte réellement effectifs (revoked_at),
    contrairement à un JWT seul qui reste valide jusqu'à expiration naturelle."""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Identifiant unique du JWT (claim "jti"), jamais le token complet : la
    # possession du JWT signé reste nécessaire, cette table ne sert qu'à savoir
    # s'il a été révoqué, pas à authentifier à elle seule.
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")
