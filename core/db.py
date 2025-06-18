from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

settings = get_settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
user_db = client[settings.user_db_name]

async def init_db() -> None:
    if "users" not in await db.list_collection_names():
        await db.create_collection("users")
