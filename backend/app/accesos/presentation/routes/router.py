
from fastapi import APIRouter

from app.accesos.presentation.routes.current_user import router as current_user_router
from app.accesos.presentation.routes.login import router as login_router

router = APIRouter(prefix="/accesos", tags=["accesos"])
router.include_router(login_router)
router.include_router(current_user_router)
