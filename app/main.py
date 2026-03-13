from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.services.cleanup_service import cleanup_expired_links, cleanup_unused_links

# Импортируем необходимые компоненты для создания таблиц
from app.db.session import engine
from app.db.base import Base
import app.models  # этот импорт нужен, чтобы все модели были загружены

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.include_router(v1_router)

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # Создание таблиц базы данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    scheduler.start()
    scheduler.add_job(cleanup_expired_links, IntervalTrigger(hours=1), id="cleanup_expired")
    scheduler.add_job(cleanup_unused_links, IntervalTrigger(days=1), id="cleanup_unused")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
async def root():
    return {"message": "URL Shortener API", "version": settings.VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)