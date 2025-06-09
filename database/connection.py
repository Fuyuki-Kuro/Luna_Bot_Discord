from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)
client: MongoClient = None
db = None

async def connect_db(uri: str, db_name: str = 'Arena'):
    global client, db
    if client is None:
        try:
            client = MongoClient(uri)
            await client.admin.command('ping')
            db = client[db_name]
            logger.info(f'Conectado ao banco de dados: {db_name}')
        except ConnectionFailure as e:
            logger.error(f'Erro ao conectar ao MONGODB: {e}')
            raise
    return db
    
async def close_db():
    global client
    if client is not None:
        client.close()
        client = None
        logger.info('Conexão com o banco de dados fechada.')

def get_db():
    if db is None:
        raise Exception('Banco de dados não conectado.')
    return db