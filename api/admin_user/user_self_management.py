# -*- coding: UTF-8 -*-
"""
@File    ：api/admin_user/user_self_management.py
@Date    ：2025/7/4 16:36
@Author  ：mxsleon
@Website ：https://mxsleon.com
"""

from typing import Literal, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from aiomysql import Pool
from core.security import get_current_user, get_password_hash
from db.database import get_db_pool, query_sql_with_params, execute_sql_with_params, query_sql
from db.jinja2_sql_auth import get_sql_query_user
from db.jinja2_sql_user import insert_into_new_user, get_user_info_sql, get_user_info_sql_all, get_user_info_sql_other, \
    update_user_info_sql, update_user_forget_password_sql
from schemas.user import UserResponse, UserCreate, RoleEnum, StatusEnum, TokenUser

# 创建路由
router = APIRouter(
    tags=["自我账户管理"],  # 分组标签
    prefix="/admin/user_self",  # 路由前缀
    responses={404: {"description": "未找到此接口"},
               500: {"description": "服务其内部错误"}}  # 全局响应
)



# 修改密码
@router.put(
    path="/change_password",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="清除用户密码",
    description="""
### 清除用户密码
此接口用于：
1. **清除用户密码**：仅当用户忘记密码时，请管理员调用此接口进行清除密码，清楚后，密码与账户一致
2. **清除登录失败标记**：重置登录尝试次数和解锁时间，通知清楚登录失败标记与时间
**权限要求**:
- 超级管理员：只有超级管理员可以调用此接口

**注意**:
- 必须同时提供用户ID和用户名，且两者必须匹配
- 操作成功后返回更新后的用户完整信息
    """,
    responses={
        200: {"description": "用户更新成功"},
        404: {"description": "用户不存在"},
        403: {"description": "无权限操作"}}
)
async def update_user_self_password(
    user_id: str = Query(..., title="用户ID", description="要更新的用户ID"),
    username: str = Query(..., title="用户名", description="要更新的用户名"),
    clean_locked: Optional[bool] = Query(True, title="清除锁定", description="设为True清除登录失败标记"),
    pool: Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    pass