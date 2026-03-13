from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from app.schemas.link import LinkCreate, LinkInfo, LinkUpdate
from app.services.link_service import LinkService
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/links", tags=["links"])

@router.post("/shorten", response_model=LinkInfo, status_code=status.HTTP_201_CREATED)
async def shorten_link(
    link_data: LinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    try:
        user_id = current_user.id if current_user else None
        link = await LinkService.create_link(db, link_data, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return link

@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_original(short_code: str, db: AsyncSession = Depends(get_db)):
    original_url = await LinkService.get_original_url(db, short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=original_url)

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        deleted = await LinkService.delete_link(db, short_code, current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Link not found")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.put("/{short_code}", response_model=LinkInfo)
async def update_link(
    short_code: str,
    link_update: LinkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        link = await LinkService.update_link(db, short_code, str(link_update.original_url), current_user.id)
        return link
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/{short_code}/stats", response_model=LinkInfo)
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    try:
        link = await LinkService.get_stats(db, short_code)
        return link
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/search", response_model=List[LinkInfo])
async def search_links(
    original_url: str = Query(..., description="Exact original URL to search for"),
    db: AsyncSession = Depends(get_db)
):
    print("Searching for links with original_url:", original_url)
    links = await LinkService.search_by_original_url(db, original_url)
    return links

@router.get("/expired", response_model=List[LinkInfo])
async def get_expired_links(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Возвращает истекшие ссылки текущего пользователя."""
    print("Fetching expired links for user_id:", current_user.id)
    now = datetime.utcnow()
    result = await db.execute(
        select(Link).where(
            Link.user_id == current_user.id,
            Link.expires_at < now
        )
    )
    print("Expired links query executed for user_id:", current_user.id)
    print(now, result)
    links = result.scalars().all()
    return links