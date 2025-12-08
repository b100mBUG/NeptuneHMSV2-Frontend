from database.models import Base
from config_db import engine
import asyncio
from sqlalchemy import text
async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def reset_database():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))

        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    
if __name__ == "__main__":
    asyncio.run(create_database())