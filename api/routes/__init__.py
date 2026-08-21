from api.routes.audit import router as audit_router
from api.routes.media import router as media_router
from api.routes.memories import router as memories_router
from api.routes.models import router as models_router
from api.routes.search import router as search_router
from api.routes.settings import router as settings_router
from api.routes.system import router as system_router

__all__ = [
    "memories_router",
    "media_router",
    "audit_router",
    "search_router",
    "system_router",
    "models_router",
    "settings_router",
]
