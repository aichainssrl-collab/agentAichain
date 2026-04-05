import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from agent_aichain.core.database import AsyncSessionLocal
from agent_aichain.core.neo4j_db import neo4j_conn
from agent_aichain.models import Tenant, Agent, Team
from agent_aichain.services.graph_service import GraphService
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# To ignore tenant context during migration
os.environ["DISABLE_TENANT_FILTER"] = "1"

async def migrate_data_to_neo4j():
    """Migrates existing relational data to Neo4j Graph Database."""
    logger.info("Avvio migrazione dati in Neo4j...")
    
    success = await neo4j_conn.connect_async()
    if not success:
        logger.error("Impossibile connettersi a Neo4j. Esco.")
        return

    await GraphService.initialize_schema()

    async with AsyncSessionLocal() as db:
        # Migrate Tenants
        logger.info("Migrazione Tenants...")
        result = await db.execute(select(Tenant))
        tenants = result.scalars().all()
        for t in tenants:
            await GraphService.sync_tenant(t.id, t.name)
            logger.info(f"Sincronizzato Tenant: {t.name} ({t.id})")

        # Migrate Agents and their tools
        logger.info("Migrazione Agents e Tool...")
        result = await db.execute(select(Agent))
        agents = result.scalars().all()
        for a in agents:
            await GraphService.sync_agent(a.id, a.name, a.tenant_id, a.role)
            if a.tools:
                for tool in a.tools:
                    await GraphService.link_agent_to_tool(a.id, tool)
            logger.info(f"Sincronizzato Agent: {a.name} ({a.id})")

        # Migrate Teams and their agents
        logger.info("Migrazione Teams...")
        result = await db.execute(select(Team).options(selectinload(Team.agents)))
        teams = result.scalars().all()
        for team in teams:
            await GraphService.sync_team(team.id, team.name, team.tenant_id)
            for agent in team.agents:
                await GraphService.link_agent_to_team(agent.id, team.id)
            logger.info(f"Sincronizzato Team: {team.name} ({team.id})")

    await neo4j_conn.close_async()
    logger.info("Migrazione dati verso Neo4j completata con successo!")

if __name__ == "__main__":
    asyncio.run(migrate_data_to_neo4j())
