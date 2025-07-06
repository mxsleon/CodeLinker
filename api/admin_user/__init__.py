# api/admin_user/_init_.py

from .user_management import router as admin_user_router
from .user_self_management import router as self_user_router


routers = [
    admin_user_router,
    self_user_router,

]
