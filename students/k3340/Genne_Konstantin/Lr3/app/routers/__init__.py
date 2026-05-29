from app.routers.auth import router as auth_router
from app.routers.workspaces import router as workspaces_router
from app.routers.tags import router as tags_router
from app.routers.tasks import router as tasks_router
from app.routers.analytics import router as analytics_router
from app.routers.parser import router as parser_router

__all__ = [
    "auth_router",
    "workspaces_router",
    "tags_router",
    "tasks_router",
    "analytics_router",
    "parser_router",
]
