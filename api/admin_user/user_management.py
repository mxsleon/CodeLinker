# -*- coding: UTF-8 -*-
"""
@File    ：api/admin_user/user_management.py
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
    tags=["用户管理"],  # 分组标签
    prefix="/admin/user",  # 路由前缀
    responses={404: {"description": "未找到此接口"},
               500: {"description": "服务其内部错误"}}  # 全局响应
)


@router.post(
    "/create",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建新用户",
    description="""
### 创建新用户
- 此接口用于在系统中注册新用户。
- 密码将以哈希形式存储在数据库中。

**注意**：
- 用户名必须是唯一的
- 传入时，有用户名唯一性检验，重复会返回**400**
- 成功创建会返回**201**，以及创建的用户信息
- 创建失败会返回**422**，以及失败具体原因

**请求体参数**以及**响应体**参数模型详见**Schemas
- 请求体**UserCreate**
- 响应体**UserResponse**
    """,
    responses={
        201: {"description": "用户创建成功"},
        400: {"description": "用户名已存在或密码不符合要求",
              "content": {"application/json": {"example": {"detail": "string"}}}},
        403: {"description": "当前身份无权限创建此级用户",
              "content": {"application/json": {"example": {"detail": "string"}}}},
        422: {"description": "请求参数验证失败", "content": {"application/json": {"example": {"detail": [
            {"type": "missing", "loc": ["body", "password"], "msg": "Field required",
             "input": {"username": "mxs", "is_active": 1, "role": "管理员"}}]}}}}}
)
async def create_user(user_data: UserCreate,
                      pool: Pool = Depends(get_db_pool),
                      current_user: dict = Depends(get_current_user)):  # JWT 验证依赖):
    """
    创建新用户的主要逻辑：
    1. 检查用户名是否已存在
    2. 验证密码复杂度
    3. 哈希密码
    4. 创建用户记录
    5. 返回用户响应
    """
    # 权限拆解
    current_user_role = current_user.get('role')
    # 传入请求体信息拆解
    create_user_name = user_data.username
    create_user_password_hash = get_password_hash(str(user_data.password))
    create_user_is_admin = 1 if user_data.role in [RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN] else 0
    create_user_is_active = user_data.is_active
    create_user_role = user_data.role
    # 1.判断是否有权限
    if RoleEnum(current_user_role).weight <= create_user_role.weight:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前身份无权限创建此级用户"
        )

    # 1. 检查用户名是否唯一
    user_name_from_db_sql = get_sql_query_user(create_user_name)
    user_name_from_db = await query_sql_with_params(pool, sql=user_name_from_db_sql, params=None)
    if user_name_from_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 6. 构建sql插入语句
    new_user_sql = insert_into_new_user(username=create_user_name,
                                        password_hash=create_user_password_hash,
                                        role=create_user_role.value,
                                        is_admin=create_user_is_admin,
                                        is_active=create_user_is_active.value)
    sql_response_num = await execute_sql_with_params(pool,sql=new_user_sql,params=None,fetch=False)
    if sql_response_num < 1 :
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'detail': f'用户创建失败，未知原因，请重试'
            }
        )
    else:

        sql_get_new_user = get_sql_query_user(username=create_user_name)
        sql_response_new_user = await execute_sql_with_params(pool=pool,sql=sql_get_new_user,params=None,fetch=True)
        return  UserResponse(**sql_response_new_user[0])


from fastapi.responses import JSONResponse


@router.get(
    path="/user_info",
    status_code=status.HTTP_200_OK,
    response_model=List[UserResponse],
    summary="获取用户信息",
    description="""
### 获取用户信息
- 此接口用于在系统中获取用户信息。
- 带有权限认证，普通用户只能查询自身信息，管理员用户可以查询所有用户和管理员信息，超级管理员可以查看所有人信息。

**注意**：
- 返回信息中，不带有敏感信息

**查询类型中**
- **self**: 查询当前用户自身信息（**忽略** query_type 和 username）
- **all**: 查询所有用户信息（**忽略** query_type 和 username），注，无权限查上级用户信息，即当角色为管理员时，无法查询超级管理员信息
- other: 查询特定用户信息（query_type 和 username）
    """,
    responses={
        200: {"description": "用户查询成功"},
        403: {"description": "无权限越级查询"},
        422: {"description": "查询参数验证失败"}}
)
async def get_user_info(query:  Literal["self", "all", "other"]  = Query(default='self', title="查询的用户，默认为自身",description="查询的类型，为空时直接返回自身信息"),
                        query_type:  Literal["exact", "fuzzy"]= Query(default='exact', title="查询类型",description="查询的类型，默认为精确查找"),
                        username: str = Query(default=None, title="查询用户名",description="查询的用户名，默认为空，当为模糊查询时，则查询所有用户名中带有username的用户"),
                      pool: Pool = Depends(get_db_pool),
                      current_user: dict = Depends(get_current_user)):  # JWT 验证依赖):
    """

    :param query:
    :param query_type:
    :param username:
    :param pool:
    :param current_user:
    :return:
    """


    # 权限拆解
    current_user_role = current_user.get('role')
    current_user_name = current_user.get('sub')
    current_user_id = current_user.get('user_id')
    role_num = RoleEnum(current_user_role).weight
    role_enum = RoleEnum(current_user_role)

    if query == 'self':
        sql_get_self = get_user_info_sql(username=current_user_name,id=current_user_id)
        data_self_info = await execute_sql_with_params(pool=pool,sql=sql_get_self,params=None,fetch=True)
        # 将查询结果转换为模型实例列表
        validated_users = [
            UserResponse(**user_data)
            for user_data in data_self_info
        ]
        return validated_users

    # 当查询类型不为自身时，通过权重判断，为普通用户返回403
    if role_num <= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前身份无权限查询"
        )
    else:
        if query == 'all':
            sql_get_all = get_user_info_sql_all(role=role_enum)
            dict_data_all_info = await execute_sql_with_params(pool=pool, sql=sql_get_all, params=None, fetch=True)
            # 将查询结果转换为模型实例列表
            validated_users = [
                UserResponse(**user_data)
                for user_data in dict_data_all_info
            ]
            return validated_users

        if query == 'other':
            sql_get_other = get_user_info_sql_other(username=username,role=role_enum,query_type=query_type)
            dict_data_other_info = await query_sql(pool=pool, sql=sql_get_other)
            # 将查询结果转换为模型实例列表
            validated_users = [
                UserResponse(**user_data)
                for user_data in dict_data_other_info
            ]
            return validated_users


@router.delete(
    path="/delete_user",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="软删除用户（封禁）",
    description="""
### 软删除用户（封禁）
- 此接口用于在系统中禁用用户（软删除）
- 带有权限认证，普通用户无权限操作，管理员用户只能封禁普通用户，超级管理员可以封禁所有用户
- 软删除操作会将用户的 `is_active` 状态从 1（激活）改为 0（禁用）

**权限要求**:
- 管理员：只能封禁比自己权限低的用户（如普通用户）
- 超级管理员：可以封禁所有用户

**注意**:
- 只有当用户ID和用户名传入且一致时，才能封禁用户
- 此操作不会物理删除用户数据，只是禁用账户
- 被封禁的用户将无法登录系统
    """,
    responses={
        200: {"description": "用户封禁成功"},
        403: {"description": "无权限操作"},
        404: {"description": "用户不存在"},
        422: {"description": "参数验证失败"}}
)
async def soft_delete_user(
    delete_type: Literal["soft"] = Query("soft", title="删除类型", description="固定为软删除"),
    user_id: str = Query(..., title="用户ID", description="要封禁的用户ID"),
    username: str = Query(..., title="查询用户名",description="要封禁的用户名"),
    pool: Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    # 权限拆解
    current_user_role = current_user.get('role')
    role_num = RoleEnum(current_user_role).weight
    role_enum = RoleEnum(current_user_role)

    # 当查询类型不为自身时，通过权重判断，为普通用户返回403
    if role_num <= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前身份无权限"
        )
    sql_get_other = get_user_info_sql_other(username=username, role=role_enum)
    list_data_user_info = await query_sql(pool=pool, sql=sql_get_other)

    if len(list_data_user_info) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到相关用户"
        )
    dict_data_user_info = list_data_user_info[0]
    delete_user_id = dict_data_user_info['id']
    delete_user_role = RoleEnum(dict_data_user_info['role'])
    if delete_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="没有找到相关用户"
        )

    if role_num <= delete_user_role.weight:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="当前身份无权限"
        )
    delete_sql = update_user_info_sql(username=username,id=user_id,is_active=StatusEnum.INACTIVE)
    result = await execute_sql_with_params(pool=pool,sql=delete_sql,params=None,fetch=False)
    if result == 1 :
        sql_get_other = get_user_info_sql_other(username=username, role=role_enum)
        list_data_user_info = await query_sql(pool=pool, sql=sql_get_other)
        return UserResponse(**list_data_user_info[0])
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="未知原因删除失败，请重试"
        )


@router.put(
    path="/update_user",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="更新用户信息",
    description="""
### 更新用户信息
此接口用于：
1. **提升用户权限**：修改用户角色（仅限管理员以上操作）
2. **解禁用户**：将用户状态从禁用(0)改为激活(1)
3. **清除登录失败标记**：重置登录尝试次数和解锁时间

**权限要求**:
- 普通用户：无权限
- 管理员：只能操作比自己权限低的用户
- 超级管理员：可以操作所有用户

**注意**:
- 必须同时提供用户ID和用户名，且两者必须匹配
- 至少需要提供以下参数之一：`new_role`、`activate` 或 `clean_locked`
- 操作成功后返回更新后的用户完整信息
- 如需封禁用户需要delete_user接口
    """,
    responses={
        200: {"description": "用户更新成功"},
        400: {"description": "无效请求参数"},
        403: {"description": "无权限操作"},
        404: {"description": "用户不存在"}}
)
async def update_user_info(
    user_id: str = Query(..., title="用户ID", description="要更新的用户ID"),
    username: str = Query(..., title="用户名", description="要更新的用户名"),
    new_role: Literal["用户", "管理员"] = Query(None, title="角色更新", description="要设置的新角色，非超管请勿传参"),
    activate: Optional[bool] = Query(True, title="激活状态", description="设为True激活用户，False则不改变用户状态"),
    clean_locked: Optional[bool] = Query(None, title="清除锁定", description="设为True清除登录失败标记"),
    pool: Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):
    # 权限拆解
    cur_user = TokenUser(**current_user)
    cur_role_num = cur_user.role_enum.weight
    cur_role_enum = cur_user.role_enum

    # 过滤普通用户
    if cur_role_num <= 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )

    # 防止非超管进行角色定义
    if new_role and cur_role_enum is not RoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )

    # 防止操作自己
    if user_id == cur_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="传入的参数无效"
        )



    # 验证至少有一个更新参数
    if new_role is None and activate is None and clean_locked is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要提供一个更新参数：new_role, activate 或 clean_locked"
        )

    # 验证传入用户是否正确
    sql_put_user_info = get_user_info_sql(id = user_id,username=username)
    result = await execute_sql_with_params(pool=pool, sql=sql_put_user_info, params=None, fetch=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


    # 进行参数转化
    if new_role is None :
        role = None
    else :
        role = RoleEnum(new_role)
    if  activate is None or activate is False:
        is_active = None
    else :
        is_active = StatusEnum(1)
    if clean_locked is None or clean_locked is False:
        clean_locked = False
    else :
        clean_locked = True
    # 进行sql拼接
    update_sql =  update_user_info_sql(id = user_id,username=username,
                                       role=role,
                                       is_active=is_active,
                                       clean_locked=clean_locked)

    user_update_sql = await execute_sql_with_params(pool=pool, sql=update_sql, params=None, fetch=False)

    if user_update_sql == 1 :
        sql_get_other = get_user_info_sql_other(username=username,role=cur_role_enum)
        list_data_user_info = await query_sql(pool=pool, sql=sql_get_other)
        return UserResponse(**list_data_user_info[0])
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="未知原因失败，请重试"
        )



# forget-password
@router.put(
    path="/forget_password",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="清除用户密码",
    description="""
### 清除用户密码
此接口用于：
1. **清除用户密码**：仅当用户忘记密码时，请管理员调用此接口进行清除密码，清除后，密码与账户一致
2. **清除登录失败标记**：重置登录尝试次数和解锁时间，通知清除登录失败标记与时间
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
async def update_user_forget_password(
    user_id: str = Query(..., title="用户ID", description="要更新的用户ID"),
    username: str = Query(..., title="用户名", description="要更新的用户名"),
    clean_locked: Optional[bool] = Query(True, title="清除锁定", description="设为True清除登录失败标记"),
    pool: Pool = Depends(get_db_pool),
    current_user: dict = Depends(get_current_user)
):

    # 权限拆解
    cur_user = TokenUser(**current_user)
    cur_role_enum = cur_user.role_enum


    # 防止非超管进行调用
    if cur_role_enum is not RoleEnum.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )


    # 验证传入用户是否正确
    sql_put_user_info = get_user_info_sql(id = user_id,username=username)
    result = await execute_sql_with_params(pool=pool, sql=sql_put_user_info, params=None, fetch=True)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )


    # 进行sql拼接
    update_sql =  update_user_forget_password_sql(id = user_id,username=username,clean_locked=clean_locked)
    user_update_sql = await execute_sql_with_params(pool=pool, sql=update_sql, params=None, fetch=False)

    if user_update_sql == 1 :
        sql_get_other = get_user_info_sql_other(username=username,role=cur_role_enum)
        list_data_user_info = await query_sql(pool=pool, sql=sql_get_other)
        return UserResponse(**list_data_user_info[0])
    else:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="未知原因失败，请重试"
        )

