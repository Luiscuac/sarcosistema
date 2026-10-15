from fastapi import APIRouter

from app.ia.presentation.routes.transcription import router as transcription_router

router = APIRouter(prefix="/ia", tags=["ia"])
router.include_router(transcription_router)
