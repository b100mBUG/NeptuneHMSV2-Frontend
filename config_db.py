from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os, sys

from appdirs import user_data_dir  

APP_NAME = "MyApp"
APP_AUTHOR = "MyCompany"

def get_db_path():
    db_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(db_dir, exist_ok=True)
    
    return os.path.join(db_dir, "database.db")

db_path = get_db_path()

DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    async with async_session() as session:
        yield session

