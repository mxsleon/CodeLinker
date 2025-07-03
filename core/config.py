# core/config.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn, AmqpDsn, validator, AnyUrl
from typing import Optional, List, Dict, Any


class Settings(BaseSettings):
    # 1. 应用基础配置
    APP_TITLE:str = 'CodeLinker API'
    APP_DESCRIPTION: str = "编码管家API接口文档"
    APP_VERSION:str = '0.3'
    ENV: str = Field("development", description="运行环境: development, staging, production")
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Shanghai"

    # 2. 服务器配置
    HOST: str = "192.168.54.7"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]

    # 3. 数据库配置
    DB_DRIVER: str = "mysql+aiomysql"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "mxs123456"
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 10
    DB_POOL_RECYCLE: int = 300  # 连接回收时间(秒)
    DB_AUTOCOMMIT: bool = True


    # # 数据库连接URL (自动生成)
    # DATABASE_URL: Optional[str] = None
    #
    # @validator("DATABASE_URL", pre=True)
    # def assemble_db_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
    #     if isinstance(v, str):
    #         return v
    #     return f"{values.get('DB_DRIVER')}://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"

    # # 4. Redis配置 (用于缓存和会话)
    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    # REDIS_PASSWORD: Optional[str] = None
    # REDIS_DB: int = 0
    # REDIS_URL: Optional[RedisDsn] = None

    # @validator("REDIS_URL", pre=True)
    # def assemble_redis_url(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
    #     if isinstance(v, str):
    #         return v
    #     password = values.get("REDIS_PASSWORD")
    #     host = values.get("REDIS_HOST")
    #     port = values.get("REDIS_PORT")
    #     db = values.get("REDIS_DB")
    #
    #     if password:
    #         return f"redis://:{password}@{host}:{port}/{db}"
    #     return f"redis://{host}:{port}/{db}"

    # 5. JWT认证配置
    JWT_SECRET: str = "mxs1233456"  # jwt_加密字符串
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 1440  # 访问令牌有效期(分钟)，24小时
    JWT_REFRESH_EXPIRE_DAYS: int = 7  # 刷新令牌有效期(天)
    JWT_VERIFY_EXP: bool = True # 是否验证令牌过期

    # 6. 安全配置
    SECURE_COOKIES: bool = False
    CSRF_PROTECTION: bool = False
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    PASSWORD_HASH_ROUNDS: int = 12

    # 7. 日志配置
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "app.log"

    # 8. 性能与缓存
    # CACHE_ENABLED: bool = True
    # CACHE_TTL: int = 300  # 缓存默认过期时间(秒)
    QUERY_TIMEOUT: int = 30  # 数据库查询超时时间(秒)

    # 9. 第三方服务集成
    SENTRY_DSN: Optional[str] = None  # 错误监控服务
    EMAIL_HOST: Optional[str] = None  # SMTP邮件服务
    EMAIL_PORT: Optional[int] = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # 10. 高级功能开关
    ENABLE_PERMISSION_CACHE: bool = True
    ENABLE_API_RATE_LIMIT: bool = False
    ENABLE_AUDIT_LOG: bool = True

    # Pydantic 配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# 使用缓存获取配置实例
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# 全局设置实例
settings = get_settings()