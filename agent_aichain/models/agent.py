from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin
from .associations import team_agents


class Agent(Base, TimestampMixin):
    """AI Agent model - tenant-scoped"""
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # Role AGNO
    model: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    tools: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Foreign keys
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="agents")
    teams: Mapped[list["Team"]] = relationship("Team", secondary=team_agents, back_populates="agents")
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="agent")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"