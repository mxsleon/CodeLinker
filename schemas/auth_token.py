from pydantic import BaseModel


class Token(BaseModel):
    """Token响应模型"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token数据模型"""

    username: str | None = None
    user_id: str | None = None
