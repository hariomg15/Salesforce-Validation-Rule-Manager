from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("oauth_sessions.id"),
        nullable=True,
    )
    object_name: Mapped[str] = mapped_column(String(255), default="Account")
    rule_name: Mapped[str] = mapped_column(String(255))
    previous_state: Mapped[str] = mapped_column(String(20))
    new_state: Mapped[str] = mapped_column(String(20))
    deploy_status: Mapped[str] = mapped_column(String(50), default="pending")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
