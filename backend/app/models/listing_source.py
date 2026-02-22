from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ListingSource(Base):
    """Mapping from canonical listing to provider source."""
    
    __tablename__ = "listing_sources"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    provider_listing_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    list_price: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    raw_payload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_payloads.id"),
        nullable=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    
    def __repr__(self) -> str:
        return f"ListingSource(id={self.id}, provider={self.provider_name}, listing_id={self.provider_listing_id})"
