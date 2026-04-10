"""Association tables for many-to-many relationships"""
from sqlalchemy import Table, Column, ForeignKey
from agent_aichain.models.base import Base

team_agents = Table(
    "team_agents",
    Base.metadata,
    Column("team_id", ForeignKey("teams.id"), primary_key=True),
    Column("agent_id", ForeignKey("agents.id"), primary_key=True),
)

agent_skills = Table(
    "agent_skills",
    Base.metadata,
    Column("agent_id", ForeignKey("agents.id"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id"), primary_key=True),
)