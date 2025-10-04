import asyncio

from app.api.v1.endpoints.simulation import get_simulation_history
from app.core.database import SessionLocal
from app.core.models import User
from fastapi import Depends

# Create DB session
session = SessionLocal()
user = session.query(User).filter(User.username == "codex_user_p5se0v").first()

async def run():
    async def get_db_override():
        try:
            yield session
        finally:
            pass
    # Call the coroutine manually by injecting dependencies
    result = await get_simulation_history(db=session, current_user=user)
    print(result)

asyncio.run(run())
