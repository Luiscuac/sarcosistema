from fastapi import APIRouter

from backend.app.ia.whisper.presentation.routes.transcription import router as transcription_router

router = APIRouter(prefix="/ia", tags=["ia"])
router.include_router(transcription_router)
