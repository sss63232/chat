from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

client: AsyncIOMotorClient | None = None
database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    global client, database

    if client is not None and database is not None:
        return

    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongo_uri)
    database = client[settings.mongo_database]
    await database.chat_messages.create_index("sessionId")
    await database.background_tasks.create_index([("userId", 1), ("createdAt", -1)])
    await database.background_tasks.create_index("status")
    await database.background_tasks.create_index("updatedAt")


async def disconnect_from_mongo() -> None:
    global client, database

    if client is not None:
        client.close()
    client = None
    database = None


def get_database() -> AsyncIOMotorDatabase:
    if database is None:
        raise RuntimeError("MongoDB is not connected")
    return database
