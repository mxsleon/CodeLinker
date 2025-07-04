# -*- coding: UTF-8 -*-
"""
@File    ：api/health_status/health.py
@Date    ：2025/7/4 16:52 
@Author  ：mxsleon
@Website ：https://mxsleon.com
"""
from datetime import datetime, timezone
import platform

import pytz
from fastapi import APIRouter, status
import psutil
import os

from core.config import settings
from schemas.health_status import StatusResponse, StatusEnum

router = APIRouter(
    tags=["系统健康状态检查"],
    prefix="/system" )

def get_system_info() -> dict:
    """获取跨平台的系统信息"""
    return {
        "os": os.name,
        "platform": platform.platform(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }


@router.get("/health", response_model=StatusResponse)
async def health_check():
    """基础健康检查 (跨平台)"""
    response = StatusResponse(
        status=StatusEnum.HEALTHY,
        timestamp=datetime.now(pytz.timezone(settings.TIMEZONE)).replace(tzinfo=None),
        error=''
    )

    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        # 内存使用
        mem = psutil.virtual_memory()

        response.details = {
            "system": get_system_info(),
            "cpu_usage": cpu_percent,
            "memory_usage": mem.percent,
            "memory_available": f"{mem.available / (1024 ** 3):.2f} GB",
            "processes": len(psutil.pids())
        }

        # 添加警告机制
        if cpu_percent > 90:
            response.status = StatusEnum.WARNING
            response.error = "High CPU usage"
        elif mem.percent > 90:
            response.status = StatusEnum.WARNING
            response.error = "High memory usage"

    except Exception as e:
        response.status = StatusEnum.ERROR
        response.error = str(e)

    return response

