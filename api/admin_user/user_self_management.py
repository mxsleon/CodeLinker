# -*- coding: UTF-8 -*-
"""
@File    ：api/admin_user/user_self_management.py
@Date    ：2025/7/4 16:36
@Author  ：mxsleon
@Website ：https://mxsleon.com
"""

from datetime import datetime, timedelta
from typing import Literal, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from aiomysql import Pool
from core.security import get_current_user, get_password_hash, verify_password
from db.database import get_db_pool, query_sql_with_params, execute_sql_with_params, query_sql
from db.jinja2_sql_auth import get_sql_query_user, update_sql_update_user
from db.jinja2_sql_user import insert_into_new_user, get_user_info_sql, get_user_info_sql_all, get_user_info_sql_other, \
    update_user_info_sql, update_user_forget_password_sql, count_username_sql, update_self_management_sql
from schemas.user import UserResponse, UserCreate, RoleEnum, StatusEnum, TokenUser

# 创建路由
router = APIRouter(
    tags=["自我账户管理"],  # 分组标签
    prefix="/admin/user_self",  # 路由前缀
    responses={404: {"description": "未找到此接口"},
               500: {"description": "服务其内部错误"}}  # 全局响应
)




@router.put(
    path="/change_username_password",
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
    # 1. 查询用户
    query_sql = get_sql_query_user(cur_user_name)

    # 2. 执行查询 - 必须使用await等待异步操作完成
    user_result = await query_sql_with_params(pool, sql=query_sql, params=None)

    # 5. 检查账户状态
    if user_result.get('is_active') == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    # 6. 检查账户锁定时间
    locked_until = user_result.get('locked_until')
    if locked_until:
        # 确保时间比较在相同时区下进行，移除了时区，默认当地时区
        current_time = datetime.now()
        print(current_time)
        # 如果locked_utc是naive时间，转换为aware时间
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace()
        # 检查是否仍在锁定期内
        if current_time < locked_until:
            remaining = locked_until - current_time
            print(remaining)
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"账户已锁定，请 {minutes} 分 {seconds} 秒后再试"
            )

    # 4. 验证密码 - 使用存储的哈希值与输入的密码比较
    if not verify_password(password,user_result.get('password_hash')):
        sql_verify_password = update_sql_update_user(id =user_result.get('id'),login_attempts='plus')
        await execute_sql_with_params(pool, sql=sql_verify_password,fetch=True)
        if user_result.get('login_attempts') >= 4 :
            # 当返回的结果中，查询出，尝试登录次数大于4（实际已经登录错了5次）
            # 获取当前时间（UTC时区）
            now = datetime.now()
            # 加上30分钟
            future_time = now + timedelta(minutes=30)
            sql_verify_password = update_sql_update_user(id=user_result.get('id'),
                                                                                 login_attempts='reset',
                                                                                 locked_until=future_time)
            await execute_sql_with_params(pool, sql=sql_verify_password, fetch=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，尝试登录次数为{user_result.get('login_attempts')+1}次，超过5次时锁定30分钟",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证成功密码，进行更新信息
    # 8. 更新登录状态
    sql_verify_password = update_sql_update_user(id=user_result.get('id'),
                                                 login_attempts='reset',
                                                 last_login=datetime.now())
    await execute_sql_with_params(pool, sql=sql_verify_password,
                                                         fetch=True)

    # 当传入新用户名时：
    if new_user_name:
        sql_count_new_user_name = count_username_sql(username=new_user_name)
        count_num = await execute_sql_with_params(pool, sql=sql_count_new_user_name,
                                                             fetch=True)
        if count_num[0].get('user_num') != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_user_name错误，已有此用户"
            )

    # 构建密码哈希值
    new_password_hash = get_password_hash(str(new_password))
    # 拼接sql
    update_user_sql = update_self_management_sql(id=cur_user_id,new_username=new_user_name,new_password=new_password_hash)
    # 执行sql
    data_update_user_sql =  await execute_sql_with_params(pool, sql=sql_verify_password,fetch=True)
    print(data_update_user_sql)







