from sqlalchemy import delete, and_
from datetime import datetime, timedelta
from db.session import AsyncSessionLocal
from models.link import Link
from core.config import settings

async def cleanup_expired_links():
    """Удаление ссылок с истекшим сроком жизни."""
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        stmt = delete(Link).where(
            Link.expires_at.is_not(None),  
            Link.expires_at < now
        )
        result = await db.execute(stmt)
        await db.commit()
        print(f"Deleted {result.rowcount} expired links") 

async def cleanup_unused_links():
    """Удаление ссылок, не использованных более UNUSED_DAYS дней."""
    async with AsyncSessionLocal() as db:
        threshold = datetime.utcnow() - timedelta(days=settings.UNUSED_DAYS)
        stmt = delete(Link).where(
            and_(
                Link.last_used_at < threshold,
                Link.last_used_at.isnot(None)
            )
        )
        await db.execute(stmt)
        await db.commit()