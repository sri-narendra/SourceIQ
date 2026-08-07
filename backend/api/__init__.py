from fastapi import APIRouter

from api.auth import router as auth_router
from api.chat import router as chat_router
from api.dashboard import router as dashboard_router
from api.documents import router as documents_router
from api.search import router as search_router
from api.users import router as users_router
from api.workspaces import router as workspaces_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(search_router)
api_router.include_router(dashboard_router)
api_router.include_router(users_router)
