from fastapi import APIRouter
from app.api.v1.endpoints import links, auth

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(links.router)