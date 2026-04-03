from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from .base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Multi-tenancy model - isolates all data per tenant"""
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_agents: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_teams: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_runs_per_month: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)  # free, pro, enterprise
    billing_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="tenant", cascade="all, delete-orphan")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, slug={self.slug})>"