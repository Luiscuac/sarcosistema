from fastapi import APIRouter

from app.ia.transcriptor.presentation.routes.router import router as transcriptor_router
from app.ia.whisper.presentation.routes.router import router as whisper_router

router = APIRouter(prefix="/ia", tags=["ia"])
router.include_router(whisper_router)
router.include_router(transcriptor_router)
