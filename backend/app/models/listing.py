from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import String, DateTime, Numeric, Integer, Text, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum

from app.models import Base


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"
    CONTINGENT = "contingent"
    FOR_RENT = "for_rent"
    RENTED = "rented"


class Listing(Base):
    """Canonical deduplicated property listing."""
    
    __tablename__ = "listings"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    canonical_key: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Address fields
    address_line1: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default="US",
    )
    
    # Location
    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=10, scale=8),
        nullable=True,
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=11, scale=8),
        nullable=True,
    )
    
    # Property details
    property_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    bedrooms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    bathrooms: Mapped[Optional[float]] = mapped_column(
        Numeric(precision=3, scale=1),
        nullable=True,
    )
    sqft: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    lot_sqft: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    year_built: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Status and pricing
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    list_price: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Timestamps
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
    
    # Additional data
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    images: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    
    __table_args__ = (
        Index('idx_listing_location', 'city', 'state'),
        Index('idx_listing_price', 'list_price'),
        Index('idx_listing_status', 'status'),
        Index('idx_listing_property_type', 'property_type'),
    )
    
    def __repr__(self) -> str:
        return f"Listing(id={self.id}, address={self.address_line1}, {self.city}, {self.state})"
    
    @property
    def address(self) -> dict:
        """Address as nested dict for schema compatibility."""
        return {
            "line1": self.address_line1,
            "line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }
    
    @property
    def location(self) -> dict:
        """Location as nested dict for schema compatibility."""
        return {
            "latitude": float(self.latitude) if self.latitude else None,
            "longitude": float(self.longitude) if self.longitude else None,
        }
    
    @property
    def details(self) -> dict:
        """Details as nested dict for schema compatibility."""
        return {
            "property_type": self.property_type,
            "bedrooms": self.bedrooms,
            "bathrooms": float(self.bathrooms) if self.bathrooms else None,
            "sqft": self.sqft,
            "lot_sqft": self.lot_sqft,
            "year_built": self.year_built,
            "description": self.description,
        }
