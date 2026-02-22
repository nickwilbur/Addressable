from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class RawPayload(Base):
    """Raw provider response data stored as JSONB."""
    
    __tablename__ = "raw_payloads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    request_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    response_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    http_status: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    response_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    response_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"RawPayload(id={self.id}, provider={self.provider_name}, status={self.http_status})"
