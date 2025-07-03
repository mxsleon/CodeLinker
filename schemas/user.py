
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


# 1. 使用枚举定义角色类型，确保只能在指定选项中选择
class RoleEnum(str, Enum):
    ADMIN = "管理员"
    USER = "用户"
    SUPER_ADMIN = "超级管理员"

    # 为角色分配权重值
    @property
    def weight(self):
        weights = {
            RoleEnum.USER: 1,
            RoleEnum.ADMIN: 2,
            RoleEnum.SUPER_ADMIN: 3
        }
        return weights[self]

    # 返回权重小于当前角色权重的角色列表
    def get_roles_with_lower_weight(self):
        return [role for role in RoleEnum if role.weight < self.weight]

    # 返回权重小于等于当前角色权重的角色列表
    def get_roles_with_lower_or_equal_weight(self):
        return [role for role in RoleEnum if role.weight <= self.weight]


# 2. 使用枚举定义状态类型
class StatusEnum(int, Enum):
    ACTIVE = 1
    INACTIVE = 0


# 2. 使用枚举定义状态类型
class AdminEnum(int, Enum):
    """
    定义是否为管理员，其中，超级管理员与管理员均为管理员
    """
    TRUE = 1
    FALSE = 0


class UserBase(BaseModel):
    username: str = Field(
        ...,
        title="用户名",
        description="用户登录名，在用户表中唯一",
        min_length=1,
        max_length=50,
        examples=["孟祥帅","mengxiangshuai"]
    )





class UserCreate(UserBase):
    password: str = Field(
        ...,
        title="密码",
        description="传入字符串，无位数限制，但不能为空",
        min_length=1,
        examples=["123456"]
    )

    # is_admin : AdminEnum = Field(
    #     AdminEnum.FALSE,
    #     title="是否为管理员",
    #     description="1代表管理员身份，只有超级管理员才可以创建，0为普通用户",
    #     examples=[1,0]
    # )

    is_active: StatusEnum = Field(
        StatusEnum.ACTIVE,  # 默认启用
        title="账户状态",
        description="1表示启用，0代表封禁",
        examples=[1,0]
    )

    role: RoleEnum = Field(
        RoleEnum.USER,
        title="用户角色",
        description="用户权限级别，只能在管理员、用户、超级管理员中选择",
        examples=["管理员","用户"]
    )




class UserUpdate(BaseModel):
    id: UUID = Field(
        ...,
        alias="user_id",
        title="用户UUID",
        description="用户的唯一标识",
    )


    password: Optional[str] = Field(
        None,
        title="新密码",
        description="新密码，传入字符串，无位数限制，但不能为空",
        min_length=1,
        examples=["123456"]
    )

    is_active: StatusEnum = Field(
        StatusEnum.ACTIVE,  # 默认启用
        title="账户状态",
        description="1表示启用，0代表封禁",
        examples=[1,0]
    )

    is_admin : int = Field(
        AdminEnum.FALSE,
        title="是否为管理员",
        description="传入整型",
        examples=[1,0]
    )



class UserResponse(UserBase):
    """用户响应模型"""
    id: UUID = Field(
        ...,
        alias="user_id",
        title="用户UUID",
        description="用户的唯一标识符，无需传入，后端自动生成",
    )

    is_admin: AdminEnum = Field(
        AdminEnum.FALSE,  # 默认非管理员
        title="管理员状态",
        description="1代表是管理员，0代表不是管理员"
    )

    role: RoleEnum = Field(
        RoleEnum.USER,
        title="用户角色",
        description="用户权限级别，只能在管理员、用户、超级管理员中选择",
        examples=["管理员","用户"]
    )

    is_active: StatusEnum = Field(
        StatusEnum.ACTIVE,  # 默认启用
        title="账户状态",
        description="1表示启用，0代表封禁",
    )

    last_login: Optional[datetime] = Field(
        None,
        title="最后登录时间",
        description="用户最后一次登录的时间戳"
    )

    created_at: Optional[datetime] = Field(
        None,
        title="创建时间",
        description="账户创建时间，由系统自动生成"
    )

    updated_at: Optional[datetime] = Field(
        None,
        title="更新时间",
        description="用户表更新时间"
    )

    locked_until: Optional[datetime] = Field(
        None,
        title="锁定时间",
        description="在锁定时间之前，用户无法登录"
    )

    login_attempts: int = Field(
        0,
        title="尝试登录次数",
        description="连续登录失败会累加，当到达5次时，账户自动锁定半个小时"
    )

    model_config = ConfigDict(
        title = "用户响应模型",
        from_attributes = True,
        validate_by_name = True,
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        },
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "孟祥帅",
                "role": "管理员",
                "is_admin": 1,
                "is_active": 1,
                "last_login": "2025-06-30 16:56:35",
                "login_attempts": 0,
                "locked_until": "2025-06-24 16:06:15",
                "created_at": "2025-06-24 16:06:15",
                "updated_at":"2025-06-24 16:06:15"
            }
        })


if __name__ == "__main__":

    a = RoleEnum.SUPER_ADMIN
    l = a.get_roles_with_lower_weight()
    for i in l:
        print(i.value)

