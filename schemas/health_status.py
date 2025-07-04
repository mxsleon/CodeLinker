# -*- coding: UTF-8 -*-
"""
@File    ：schemas/health_status.py
@Date    ：2025/7/4 16:52 
@Author  ：mxsleon
@Website ：https://mxsleon.com
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class StatusEnum(str, Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    ERROR = "error"
    OK = "ok"


class StatusResponse(BaseModel):
    """服务器状态统一响应模型"""
    status: StatusEnum = Field(
        ...,
        title="整体状态",
        description="服务的整体健康状态",
        examples=["healthy", "warning", "unhealthy"]
    )

    timestamp: datetime = Field(
        ...,
        title="时间戳",
        description="状态检查的时间点",
        examples=["2023-08-15T12:34:56.789Z"]
    )

    details: Dict[str, Any] = Field(
        default_factory=dict,
        title="详细状态",
        description="具体的状态指标和详细信息"
    )

    error: Optional[str] = Field(
        None,
        title="错误信息",
        description="当状态不正常时的错误描述",
        examples=["High CPU usage"]
    )

    # 配置模型行为
    model_config = ConfigDict(
        title="服务器状态响应",
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2023-08-15T12:34:56.789Z",
                "details": {
                    "system": {
                        "os": "Windows",
                        "platform": "Windows-10-10.0.19045-SP0",
                        "release": "10",
                        "version": "10.0.19045",
                        "machine": "AMD64",
                        "processor": "Intel64 Family 6 Model 158 Stepping 10, GenuineIntel"
                    },
                    "cpu": {
                        "cores": 8,
                        "logical_cores": 16,
                        "usage": 15.2
                    },
                    "memory": {
                        "total": "31.21 GB",
                        "available": "15.43 GB",
                        "used": "15.78 GB",
                        "percent": 50.5
                    }
                }
            }
        }
    )
