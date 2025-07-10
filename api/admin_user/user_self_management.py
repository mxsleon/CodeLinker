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




@router.put(
    path="/change_password",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="用户修改账户名或密码",
    description="""
### 用户修改账户名或密码
此接口用于（用户调用）：
1. **修改用户账户名或密码**：用户可以调用此接口进行账户名和密码的修改

**权限要求**:
- 无

**注意**:
- 必须再次验证用户名和密码，通过后，可更新
- 传递参数时，如不传参数，则默认不变，新的用户名和密码不可同时为空
    """,
    responses={
        200: {"description": "用户更新成功"},
        401: {"description": "旧密码错误"},
        400: {"description": "传入参数错误"},
        403: {"description": "账户已被禁用"},
        423: {"description": "账户已锁定"}}
)
async def update_user_self_password(
        password: str = Query(..., title="旧密码", description="用于验证身份的旧密码"),
        pool: Pool = Depends(get_db_pool),
        current_user: dict = Depends(get_current_user),
        new_user_name: str = Query(None, title="新用户名", description="需要更新的用户名"),
        new_password: str = Query(None, title="新密码", description="需要设置的新密码"),
):
    # 权限拆解
    cur_user = TokenUser(**current_user)
    cur_user_id = cur_user.user_id
    cur_user_name = cur_user.sub

    # 验证传入
    if new_user_name is None and  new_password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个更新参数：new_user_name,new_password"
        )


    # 验证旧密码是否正确
    sql_put_user_info = get_user_info_sql(id = cur_user_id,username=cur_user_id)
    result = await execute_sql_with_params(pool=pool, sql=sql_put_user_info, params=None, fetch=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    get_user_info_sql()
