from motor.motor_asyncio import AsyncIOMotorClient
from config import get_settings
from pymongo import ASCENDING

settings = get_settings()
client = AsyncIOMotorClient(settings.mongodb_uri)
admin_db = client[settings.admin_db_name]

async def init_db() -> None:
    if "users" not in await admin_db.list_collection_names():
        await admin_db.create_collection("users")
    if "patients" not in await admin_db.list_collection_names():
        await admin_db.create_collection("patients")
        
async def ensure_indexes() -> None:
    await admin_db.users.create_index(
        [   
            ("userId", 1),
            ("name.firstName", 1),
            ("name.lastName", 1),
            ("phoneNum", 1),
            ("email", 1),
        ],
        unique=True,
        name="unique_id_name_phone_email",
    )

    await admin_db.users.create_index(
        [("userId", 1)],
        unique=True,
        name="unique_userId",
    )

    await admin_db.users.create_index(
        "email", unique=True, name="unique_email"
    )
