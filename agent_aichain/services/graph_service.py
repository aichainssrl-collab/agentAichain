import logging
from agent_aichain.core.neo4j_db import neo4j_conn

logger = logging.getLogger(__name__)

class GraphService:
    @staticmethod
    async def initialize_schema():
        """
        Creates indexes and constraints for Neo4j models (N6)
        """
        driver = neo4j_conn.get_async_driver()
        if not driver:
            logger.warning("Neo4j non è connesso, skip schema initialization.")
            return

        queries = [
            "CREATE CONSTRAINT tenant_id_unique IF NOT EXISTS FOR (t:Tenant) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT team_id_unique IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT tool_name_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE",
            "CREATE INDEX agent_tenant_id_index IF NOT EXISTS FOR (a:Agent) ON (a.tenant_id)",
            "CREATE INDEX team_tenant_id_index IF NOT EXISTS FOR (t:Team) ON (t.tenant_id)"
        ]

        async with driver.session() as session:
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.error(f"Errore durante l'inizializzazione dello schema Neo4j: {e}")
        
        logger.info("Schema Neo4j inizializzato correttamente.")

    @staticmethod
    async def sync_tenant(tenant_id: int, name: str):
        """Syncs a Tenant node"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return
        query = """
        MERGE (t:Tenant {id: $id})
        SET t.name = $name
        """
        async with driver.session() as session:
            await session.run(query, id=tenant_id, name=name)

    @staticmethod
    async def sync_agent(agent_id: int, name: str, tenant_id: int, role: str = None):
        """Syncs an Agent node and its BELONGS_TO relationship to the Tenant"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return
        query = """
        MERGE (a:Agent {id: $agent_id})
        SET a.name = $name, a.tenant_id = $tenant_id, a.role = $role
        WITH a
        MATCH (t:Tenant {id: $tenant_id})
        MERGE (a)-[:BELONGS_TO]->(t)
        """
        async with driver.session() as session:
            # We also ensure the tenant exists just in case
            await GraphService.sync_tenant(tenant_id, f"Tenant {tenant_id}")
            await session.run(query, agent_id=agent_id, name=name, tenant_id=tenant_id, role=role)

    @staticmethod
    async def sync_team(team_id: int, name: str, tenant_id: int):
        """Syncs a Team node and its BELONGS_TO relationship to the Tenant"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return
        query = """
        MERGE (team:Team {id: $team_id})
        SET team.name = $name, team.tenant_id = $tenant_id
        WITH team
        MATCH (t:Tenant {id: $tenant_id})
        MERGE (team)-[:BELONGS_TO]->(t)
        """
        async with driver.session() as session:
            await GraphService.sync_tenant(tenant_id, f"Tenant {tenant_id}")
            await session.run(query, team_id=team_id, name=name, tenant_id=tenant_id)

    @staticmethod
    async def link_agent_to_team(agent_id: int, team_id: int):
        """Creates a PART_OF relationship between Agent and Team"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return
        query = """
        MATCH (a:Agent {id: $agent_id})
        MATCH (t:Team {id: $team_id})
        MERGE (a)-[:PART_OF]->(t)
        """
        async with driver.session() as session:
            await session.run(query, agent_id=agent_id, team_id=team_id)

    @staticmethod
    async def link_agent_to_tool(agent_id: int, tool_name: str):
        """Syncs a Tool node and links an Agent to it via USES_TOOL"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return
        query = """
        MERGE (t:Tool {name: $tool_name})
        WITH t
        MATCH (a:Agent {id: $agent_id})
        MERGE (a)-[:USES_TOOL]->(t)
        """
        async with driver.session() as session:
            await session.run(query, agent_id=agent_id, tool_name=tool_name)

    @staticmethod
    async def get_similar_agents(agent_id: int, tenant_id: int, limit: int = 5):
        """Finds similar agents in the same tenant based on shared tools (N4)"""
        driver = neo4j_conn.get_async_driver()
        if not driver: return []
        
        # This Cypher query finds agents in the same tenant that share the most tools with the target agent
        query = """
        MATCH (target:Agent {id: $agent_id, tenant_id: $tenant_id})-[:USES_TOOL]->(t:Tool)<-[:USES_TOOL]-(other:Agent {tenant_id: $tenant_id})
        WHERE target.id <> other.id
        WITH other, count(t) as shared_tools
        ORDER BY shared_tools DESC
        LIMIT $limit
        RETURN other.id as agent_id, other.name as name, shared_tools
        """
        
        results = []
        async with driver.session() as session:
            records = await session.run(query, agent_id=agent_id, tenant_id=tenant_id, limit=limit)
            async for record in records:
                results.append({
                    "agent_id": record["agent_id"],
                    "name": record["name"],
                    "shared_tools": record["shared_tools"]
                })
                
        return results
