# api/auth.py

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm


# 导入项目模块
from core.security import verify_password, create_access_token
from schemas.auth_token import Token
from db.database import get_db_pool, query_sql_with_params, execute_sql_with_params
from aiomysql import Pool
from db.jinja2_sql_auth import get_sql_query_user, update_sql_update_user


router = APIRouter(tags=["登录认证"])


@router.post(
    "/login",
    response_model=Token,
    summary="用户登录认证",
    description="""
## 详细描述
- **grant_type**应为password，默认为password
- **username**和**password**应传入实际值，字符串，测试时可传入管理员账号进行全部接口测试
- scope、client_id、client_secret可选择**Send empty value**按钮传空
- 测试其他接口时，应选择**Authorize**挂载依赖
- 超过5次**登录失败**锁定30分钟

## 返回
- **access_token**: JWT访问令牌
- **token_type**: 令牌类型 (bearer)
""",
    responses={
        200: {"description": "成功登录"},
        401: {
            "description": "用户名或密码错误",
            "content": {
                "application/json": {"example": {"detail": "用户名或密码错误"}}
            },
        },
        403: {
            "description": "账户已被禁用",
            "content": {"application/json": {"example": {"detail": "账户已被禁用"}}},
        },
        422: {
            "description": "参数校验失败",
            "content": {"application/json": {"example": {"detail": "参数校验失败"}}},
        },
        423: {
            "description": "账户已锁定",
            "content": {"application/json": {"example": {"detail": "账户已锁定"}}},
        },
    },
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), pool: Pool = Depends(get_db_pool)
):
    """
    用户登录接口，验证用户名密码后返回JWT令牌
    参数:
    - **username**: 用户名
    - **password**: 密码
    返回:
    - **access_token**: JWT访问令牌
    - **token_type**: 令牌类型 (bearer)
    """
    # 直接访问 form_data 的属性获取用户名和密码
    username = form_data.username
    password = form_data.password

    # 1. 查询用户
    query_sql = get_sql_query_user(username)

    # 2. 执行查询 - 必须使用await等待异步操作完成
    user_result = await query_sql_with_params(pool, sql=query_sql, params=None)

    # 3. 用户不存在
    if not user_result:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. 检查账户状态
    if user_result.get("is_active") == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用"
        )

    # 6. 检查账户锁定时间
    locked_until = user_result.get("locked_until")
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
                detail=f"账户已锁定，请 {minutes} 分 {seconds} 秒后再试",
            )

    # 4. 验证密码 - 使用存储的哈希值与输入的密码比较
    if not verify_password(password, user_result.get("password_hash")):
        # if not password == user_result['password_hash']:
        sql_verify_password = update_sql_update_user(
            id=user_result.get("id"), login_attempts="plus"
        )
        user_verify_password = await execute_sql_with_params(
            pool, sql=sql_verify_password, fetch=True
        )
        if user_result.get("login_attempts") >= 4:
            # 当返回的结果中，查询出，尝试登录次数大于4（实际已经登录错了5次）
            # 获取当前时间（UTC时区）
            now = datetime.now()
            # 加上30分钟
            future_time = now + timedelta(minutes=30)
            sql_verify_password = update_sql_update_user(
                id=user_result.get("id"),
                login_attempts="reset",
                locked_until=future_time,
            )
            user_verify_password = await execute_sql_with_params(
                pool, sql=sql_verify_password, fetch=True
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，尝试登录次数为{user_result.get('login_attempts')+1}次，超过5次时锁定30分钟",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 7. 生成JWT令牌
    access_token = create_access_token(
        data={
            "sub": username,
            "user_id": user_result.get("id"),
            "role": user_result.get("role"),
            "admin": True if user_result.get("is_admin") == 1 else False,
        }
    )

    # 8. 更新登录状态
    sql_verify_password = update_sql_update_user(
        id=user_result.get("id"), login_attempts="reset", last_login=datetime.now()
    )
    user_verify_password = await execute_sql_with_params(
        pool, sql=sql_verify_password, fetch=True
    )
    return {"access_token": access_token, "token_type": "bearer"}
