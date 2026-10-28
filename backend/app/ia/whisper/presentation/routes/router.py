from fastapi import APIRouter

from app.ia.whisper.presentation.routes.transcription import router as transcription_router

# El prefijo /ia lo aplica app.ia.router (composición única del módulo).
router = APIRouter(tags=["ia"])
router.include_router(transcription_router)
