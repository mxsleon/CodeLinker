# api/__init__.py

from .auth import router as login_router
from .admin_user import routers as admin_user_router



routers = [


    login_router,

]

for r in admin_user_router:
    routers.append(r)