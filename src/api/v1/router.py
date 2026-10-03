from fastapi import APIRouter

from src.api.v1.accounts import router as accounts_router
from src.api.v1.analytics import router as analytics_router
from src.api.v1.auth import router as auth_router
from src.api.v1.trades import router as trades_router
from src.api.v1.ws import router as ws_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(trades_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(ws_router)
