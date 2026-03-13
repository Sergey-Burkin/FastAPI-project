import random
import string
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.link import Link
from app.schemas.link import LinkCreate
from app.db.redis_client import redis_client

class LinkService:
    @staticmethod
    async def generate_unique_code(db: AsyncSession) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            result = await db.execute(select(Link).where(Link.short_code == code))
            if not result.scalar_one_or_none():
                return code

    @staticmethod
    async def create_link(db: AsyncSession, link_data: LinkCreate, user_id: Optional[int] = None) -> Link:
        short_code = link_data.custom_alias or await LinkService.generate_unique_code(db)
        if link_data.custom_alias:
            result = await db.execute(select(Link).where(Link.short_code == short_code))
            if result.scalar_one_or_none():
                raise ValueError("Custom alias already exists")
        db_link = Link(
            original_url=str(link_data.original_url),
            short_code=short_code,
            expires_at=link_data.expires_at,
            user_id=user_id
        )
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link

    @staticmethod
    async def get_original_url(db: AsyncSession, short_code: str) -> Optional[str]:
        cached = await redis_client.get(f"link:{short_code}")
        if cached:
            await db.execute(
                update(Link)
                .where(Link.short_code == short_code)
                .values(clicks=Link.clicks + 1, last_used_at=datetime.utcnow())
            )
            await db.commit()
            return cached

        result = await db.execute(
            select(Link).where(
                Link.short_code == short_code,
                Link.is_active == True,
                (Link.expires_at.is_(None) | (Link.expires_at > datetime.utcnow()))
            )
        )
        link = result.scalar_one_or_none()
        if not link:
            return None

        link.clicks += 1
        link.last_used_at = datetime.utcnow()
        await db.commit()

        await redis_client.setex(f"link:{short_code}", 3600, link.original_url)
        return link.original_url

    @staticmethod
    async def delete_link(db: AsyncSession, short_code: str, user_id: int) -> bool:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one_or_none()
        if not link:
            return False
        if link.user_id is not None and link.user_id != user_id:
            raise PermissionError("You don't have permission to delete this link")
        await db.delete(link)
        await db.commit()
        await redis_client.delete(f"link:{short_code}")
        return True

    @staticmethod
    async def update_link(db: AsyncSession, short_code: str, new_url: str, user_id: int) -> Link:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one_or_none()
        if not link:
            raise ValueError("Link not found")
        if link.user_id is not None and link.user_id != user_id:
            raise PermissionError("You don't have permission to update this link")
        link.original_url = new_url
        await db.commit()
        await db.refresh(link)
        await redis_client.delete(f"link:{short_code}")
        return link

    @staticmethod
    async def get_stats(db: AsyncSession, short_code: str) -> Link:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalar_one_or_none()
        if not link:
            raise ValueError("Link not found")
        return link

    @staticmethod
    async def search_by_original_url(db: AsyncSession, original_url: str) -> List[Link]:
        print("Searching for links with original_url:", original_url)
        result = await db.execute(
            select(Link).where(Link.original_url == original_url)
        )
        return result.scalars().all()