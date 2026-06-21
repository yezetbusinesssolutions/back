import asyncio
import sys
import os

sys.path.insert(0, '/')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.database import engine, Base
from api.models.user import User
import bcrypt
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import text

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FULL_NAME = "System Administrator"

async def main():
    print("Seeding admin user...\n")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  Tables ensured.\n")
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(
            text("SELECT user_id FROM users WHERE username = :username"),
            {"username": ADMIN_USERNAME}
        )
        if result.fetchone():
            print(f"  Admin user '{ADMIN_USERNAME}' already exists, skipping.")
        else:
            admin = User(
                username=ADMIN_USERNAME,
                full_name=ADMIN_FULL_NAME,
                role="Admin",
                assigned_site_id=None,
                password_hash=bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
            )
            session.add(admin)
            await session.commit()
            print(f"  Created admin user: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    
    await engine.dispose()
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
