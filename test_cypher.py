import asyncio
from agent_aichain.core.neo4j_db import neo4j_conn

async def test_query():
    await neo4j_conn.connect_async()
    driver = neo4j_conn.get_async_driver()
    
    tenant_id = 1
    
    query = """
    MATCH (n)
    WHERE (n:Tenant AND n.id = $tenant_id) OR n.tenant_id = $tenant_id
    WITH collect(n) as nodes_list
    
    MATCH (n)
    WHERE (n:Tenant AND n.id = $tenant_id) OR n.tenant_id = $tenant_id
    OPTIONAL MATCH (n)-[r]->(m)
    WHERE (m:Tenant AND m.id = $tenant_id) OR m.tenant_id = $tenant_id OR m:Tool
    
    RETURN n, r, m
    """
    
    query2 = """
    MATCH (n)
    WHERE (n:Tenant AND n.id = $tenant_id) OR n.tenant_id = $tenant_id
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n, r, m
    """
    
    async with driver.session() as session:
        records = await session.run(query2, tenant_id=tenant_id)
        async for record in records:
            print(record)
            
    await neo4j_conn.close_async()

if __name__ == "__main__":
    asyncio.run(test_query())
