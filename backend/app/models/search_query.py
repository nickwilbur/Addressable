from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.models import Base


class SearchMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class SearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchQuery(Base):
    """User search query with criteria and execution status."""
    
    __tablename__ = "search_queries"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    criteria_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    mode: Mapped[SearchMode] = mapped_column(
        SQLEnum(SearchMode),
        nullable=False,
        default=SearchMode.SYNC,
    )
    status: Mapped[SearchStatus] = mapped_column(
        SQLEnum(SearchStatus),
        nullable=False,
        default=SearchStatus.PENDING,
    )
    error_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    total_providers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    completed_providers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_listings: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    
    def __repr__(self) -> str:
        return f"SearchQuery(id={self.id}, status={self.status}, mode={self.mode})"
