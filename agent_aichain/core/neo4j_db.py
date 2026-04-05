from neo4j import GraphDatabase, AsyncGraphDatabase
from agent_aichain.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__password = pwd
        self.__driver = None
        self.__async_driver = None

    def connect(self):
        try:
            self.__driver = GraphDatabase.driver(
                self.__uri, auth=(self.__user, self.__password)
            )
            # Verifica connessione
            self.__driver.verify_connectivity()
            logger.info("Connessione a Neo4j stabilita con successo.")
            return True
        except Exception as e:
            logger.error(f"Errore di connessione a Neo4j: {e}")
            return False

    async def connect_async(self):
        try:
            self.__async_driver = AsyncGraphDatabase.driver(
                self.__uri, auth=(self.__user, self.__password)
            )
            await self.__async_driver.verify_connectivity()
            logger.info("Connessione asincrona a Neo4j stabilita con successo.")
            return True
        except Exception as e:
            logger.error(f"Errore di connessione asincrona a Neo4j: {e}")
            return False

    def close(self):
        if self.__driver is not None:
            self.__driver.close()
            logger.info("Connessione a Neo4j chiusa.")

    async def close_async(self):
        if self.__async_driver is not None:
            await self.__async_driver.close()
            logger.info("Connessione asincrona a Neo4j chiusa.")

    def get_driver(self):
        return self.__driver

    def get_async_driver(self):
        return self.__async_driver


# Istanza singleton globale
neo4j_conn = Neo4jConnection(
    settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
)

async def get_neo4j_session():
    """Dependency per FastAPI che fornisce una sessione asincrona Neo4j"""
    if not neo4j_conn.get_async_driver():
        success = await neo4j_conn.connect_async()
        if not success:
            raise Exception("Impossibile connettersi a Neo4j")
        
    async with neo4j_conn.get_async_driver().session() as session:
        yield session
