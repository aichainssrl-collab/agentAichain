"""Skill model — catalog of agent capabilities inspired by OpenClaw/ClaHub.

Skills are discovered by agents at runtime and mapped to Agno Tool instances.
Each skill can optionally define which Agno toolkit class implements it.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from .base import Base


# ── Category taxonomy (OpenClaw-inspired) ──────────────────────────────────
SKILL_CATEGORIES = [
    # Core
    "productivity",
    "development",
    "communication",
    "research",
    "ai_models",
    # Business
    "marketing",
    "sales",
    "finance",
    "support",
    # Cloud & Infra
    "cloud",
    "devops",
    "security",
    "data",
    # Content & Media
    "content",
    "social_media",
    "media_generation",
    # Utility
    "integration",
    "automation",
    "iot",
    "custom",
]


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)  # one of SKILL_CATEGORIES
    # The Agno tool class name this skill maps to (e.g. "DuckDuckGoTools", "CalculatorTools")
    agno_tool_class = Column(String(200), nullable=True)
    # Extra parameters passed when instantiating the tool (JSON string)
    agno_tool_params = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
