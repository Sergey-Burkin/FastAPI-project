from fastapi import FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from api.v1.router import router as v1_router
from core.config import settings
from services.cleanup_service import cleanup_expired_links, cleanup_unused_links
from datetime import datetime
from db.session import get_db
from db.session import engine
from db.base import Base
from services.link_service import LinkService

import models  

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.include_router(v1_router)

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # Создание таблиц базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    scheduler.start()
    scheduler.add_job(cleanup_expired_links, IntervalTrigger(hours=1), next_run_time=datetime.now(),  id="cleanup_expired")
    scheduler.add_job(cleanup_unused_links, IntervalTrigger(days=1), next_run_time=datetime.now(), id="cleanup_unused")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# Эндпоинт редиректа вынесен сюда, чтобы *короткие* ссылки были вида service.com/{short_code},
# а не service.com/v1/links/{short_code}.
@app.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT) 
async def redirect_to_original(short_code: str, db: AsyncSession = Depends(get_db)):
    original_url = await LinkService.get_original_url(db, short_code)
    if not original_url:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=original_url)

@app.get("/")
async def root():
    return {"message": "URL Shortener API", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)