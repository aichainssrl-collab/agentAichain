from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # e.g., "gpt-4", "claude-3-opus", "llama2"
    provider = Column(String(50), nullable=False)  # "openai", "anthropic", "google", "ollama", "openrouter", etc.
    base_url = Column(String(500), nullable=True)  # API endpoint URL, e.g., http://localhost:11434 for Ollama
    api_key = Column(String(200), nullable=True)   # API key for provider (if required)
    max_tokens = Column(Integer, nullable=True)  # max completion tokens
    max_context = Column(Integer, nullable=True)  # context window size
    cost_per_1k_input = Column(Float, nullable=True)  # cost per 1K input tokens
    cost_per_1k_output = Column(Float, nullable=True)  # cost per 1K output tokens
    config = Column(Text, nullable=True)  # JSON config for additional parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="ai_models")

    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='uq_aimodel_name_tenant'),
    )
