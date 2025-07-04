# core/security.py
from zoneinfo import ZoneInfo

import bcrypt
from datetime import datetime, timedelta,timezone

import pytz

from core.config import settings


def verify_password( password: str, hashed_password: str) -> bool:
    """
    验证密码是否与哈希值匹配

    Args:
        password: 明文密码字符串
        hashed_password: 已加密的密码字符串

    Returns:
        如果匹配返回True，否则返回False
    """
    # 将明文密码和哈希密码转换为字节
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    # 验证密码
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str,rounds: int = settings.PASSWORD_HASH_ROUNDS) -> str:
    """

    :param password: 传入明文字符串
    :param rounds: 获取系统配置
    :return: 返回加密字符串
    """
    # 将明文密码转换为字节
    password_bytes = password.encode('utf-8')
    # 生成盐值并进行哈希
    salt = bcrypt.gensalt(rounds=rounds)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # 将字节转换为字符串返回
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire =  datetime.now(pytz.timezone(settings.TIMEZONE)) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )



from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="令牌已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    invalid_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )
    missing_fields_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="令牌缺少必要字段",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码 JWT 令牌
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": settings.JWT_VERIFY_EXP}
        )



        # 验证必要字段是否存在
        required_fields = ["sub", "user_id", "admin", "role"]
        if not all(field in payload for field in required_fields):
            raise missing_fields_exception

        # 创建包含所有payload字段的用户字典
        user_data = {**payload, "username": payload.get("sub")}

        # 返回包含用户信息的字典
        return user_data

    except ExpiredSignatureError:
        raise expired_exception
    except JWTError as e:
        if "Signature verification failed" in str(e):
            raise invalid_token_exception
        raise credentials_exception
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )





# # 同步测试函数
# def test_token_generation():
#     # 生成令牌
#     token = create_access_token(data)
#     print(f"生成的JWT: {token}")
#
#     try:
#         # 同步调用验证函数
#         user_data = get_current_user(token=token)
#         print(f"解码后的用户数据: {user_data}")
#     except Exception as e:
#         print(f"验证失败: {e}")
#
#
# # 异步测试函数(如果get_current_user是异步的)
# async def test_token_generation_async():
#     token = create_access_token(data)
#     print(f"生成的JWT: {token}")
#
#     try:
#         # 异步调用验证函数
#         user_data = await get_current_user(token=token)
#         print(f"解码后的用户数据: {user_data}")
#     except Exception as e:
#         print(f"验证失败: {e}")

if __name__ == "__main__":
    pass
    #
    # print(verify_password("mxs123",'$2b$12$rHgnhosK1vE4Gaasa3Trk.6QGRVFNc4IVEDghTY6JsH5fMiaQJ7oK'))
    # required_fields = ["sub", "user_id", "admin", "role"]
    #
    # data = {
    #     'sub':'mxs',
    #     'admin':True,
    #     'role': 1,
    #     'user_id':'123'
    #
    # }
    #
    #
    # # 运行同步测试
    # asyncio.run(test_token_generation_async())
    #
    # from datetime import datetime, timedelta
    # import pytz
    #
    # # 假设settings.TIMEZONE是IANA时区名称，例如 "Asia/Shanghai"
    # expire = datetime.now(pytz.timezone(settings.TIMEZONE)) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    #
    # print(expire)