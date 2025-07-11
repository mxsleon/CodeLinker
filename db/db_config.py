# db/db_config.py
import re
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any


def sanitize_identifier(identifier: str) -> str:
    """安全处理数据库标识符（表名、列名）"""
    # 只允许字母、数字、下划线和点
    if not re.match(r"^[\w\.]+$", identifier):
        raise ValueError(f"Invalid identifier: {identifier}")

    # 分割数据库名和表名（如果存在点分隔）
    parts = identifier.split(".")
    # 用反引号包裹每个部分
    return ".".join([f"`{part}`" for part in parts])


class DbSettings(BaseSettings):
    # 设置系统数据库表格
    # 用户表格
    USER_TABLE: str = """cl_system_settings.system_user"""

    # 编码管理表格
    CODE_MANAGEMENT_TABLE: str = """cl_code_managerment.code_table_management"""

    # 账单管理表
    ORDER_MANAGEMENT_TABLE: str = """cl_order.order_table_management"""


# 使用缓存获取配置实例
@lru_cache()
def get_db_settings() -> DbSettings:
    return DbSettings()


# 全局设置实例
db_settings = get_db_settings()
