import asyncio
from db.models import create_db_and_tables

asyncio.run(create_db_and_tables())
