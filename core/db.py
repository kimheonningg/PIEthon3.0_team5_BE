from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings

settings = get_settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
admin_db = client[settings.admin_db_name]

async def init_db() -> None:
    if "users" not in await admin_db.list_collection_names():
        await admin_db.create_collection("users")
