from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from .associations import team_agents


class Team(Base, TimestampMixin):
    """Team model - group of agents working together"""
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(50), default="coordinate", nullable=False)  # coordinate, route, collaborate
    max_iterations: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Foreign keys
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="teams")
    agents: Mapped[list["Agent"]] = relationship("Agent", secondary="team_agents", back_populates="teams")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="team")