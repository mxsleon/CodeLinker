# main.py
# mxsleon

import uvicorn
from db.database import  init_db, close_db
import fastapi_cdn_host
from contextlib import asynccontextmanager
from api import routers
from core.config import settings
from fastapi import  Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware





# 使用异步上下文管理器管理应用生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        print("✅ 数据库连接池初始化成功")
    except Exception as e:
        print(f"❌ 数据库连接池初始化失败: {str(e)}")
        raise
    yield
    try:
        await close_db()
        print("✅ 数据库连接池已关闭")
    except Exception as e:
        print(f"❌ 关闭数据库连接池时出错: {str(e)}")


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,  # 注册生命周期管理器
    docs_url=None,  # 禁用默认的/docs路由
)

fastapi_cdn_host.patch_docs(app)

# 添加Gzip中间件压缩
app.add_middleware(GZipMiddleware, minimum_size=500)



# 循环汇总api中所有的分路由
for router in routers:
    app.include_router(router)


# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """
    自定义Swagger UI页面，使用本地静态资源
    """
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=settings.APP_TITLE + " - Swagger UI",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon.png",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        init_oauth=app.swagger_ui_init_oauth,
        # 添加自定义配置
        swagger_ui_parameters={
            "dom_id": "#swagger-ui",
            "layout": "BaseLayout",
            "deepLinking": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "syntaxHighlight.theme": "dark",
            "tryItOutEnabled": True,
        }
    )






if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS
    )