from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Text, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.models import Base


class ProviderRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ProviderRun(Base):
    """Execution of a single provider for a search query."""
    
    __tablename__ = "provider_runs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    search_query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("search_queries.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[ProviderRunStatus] = mapped_column(
        SQLEnum(ProviderRunStatus),
        nullable=False,
        default=ProviderRunStatus.PENDING,
    )
    error_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    request_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    raw_payload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_payloads.id"),
        nullable=True,
    )
    listings_found: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"ProviderRun(id={self.id}, provider={self.provider_name}, status={self.status})"
