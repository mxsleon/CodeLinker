# db/database.py
import asyncio

import aiomysql
from aiomysql import Pool
from typing import Optional

from core.config import settings

# 创建连接mysql数据库参数字典
# 从配置中获取数据库参数
DB_CONFIG = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "minsize": settings.DB_POOL_MIN,
    "maxsize": settings.DB_POOL_MAX,
    "autocommit": settings.DB_AUTOCOMMIT,
    "pool_recycle": settings.DB_POOL_RECYCLE  # 连接回收时间
}


pool: Optional[Pool] = None

async def get_db_pool() -> Pool:
    """获取数据库连接池"""
    if pool is None:
        raise RuntimeError("数据库连接池未初始化")
    return pool

async def init_db() -> None:
    """初始化数据库连接池"""
    global pool
    try:
        print('🔄 正在初始化数据库连接池...')
        pool = await aiomysql.create_pool(**DB_CONFIG)
        print('✅ 数据库连接池初始化完成')
    except Exception as e:
        print(f"❌ 数据库连接池初始化失败: {str(e)}")
        raise

async def close_db() -> None:
    """关闭数据库连接池"""
    global pool
    if pool:
        print('🛑 正在关闭数据库连接池...')
        pool.close()
        await pool.wait_closed()
        pool = None
        print('✅ 数据库连接池已关闭')


# 执行sql查询异步函数
async def query_sql(pool: Pool, sql: str):
    """执行SQL查询"""
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:  # 返回字典格式结果
            await cursor.execute(sql)
            # 返回sql查询后的数据
            return await cursor.fetchall()


async def query_sql_with_params(
    pool: Pool,
    sql: str,
    params: list = None
):
    """
    执行参数化SQL查询（使用位置参数）

    :param pool: 数据库连接池
    :param sql: SQL查询语句（使用 %s 占位符）
    :param params: 参数列表，顺序与SQL中的占位符匹配
    :return: 查询结果（字典）
    """
    if params is None:
        params = []

    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 执行参数化查询
            await cursor.execute(sql, params)
            result = await cursor.fetchone()
            return result


async def execute_sql_with_params(
        pool: Pool,
        sql: str,
        params: list = None,
        fetch: bool = False
):
    """
    执行参数化SQL操作（使用位置参数）

    :param pool: 数据库连接池
    :param sql: SQL语句（使用 %s 占位符）
    :param params: 参数列表
    :param fetch: 是否获取结果集（用于查询）
    :return:
        - 如果 fetch=True: 返回结果集（字典列表）
        - 否则: 返回受影响的行数
    """
    if params is None:
        params = []
    async with pool.acquire() as conn:
        cursor_type = aiomysql.DictCursor if fetch else aiomysql.Cursor
        async with conn.cursor(cursor_type) as cursor:
            # 执行SQL
            await cursor.execute(sql, params)
            # 处理结果
            if fetch:
                result = await cursor.fetchall()
            else:
                result = cursor.rowcount
            await conn.commit()
            return result


if __name__ == "__main__":
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    sql = "SELECT field_name FROM `cl_code_managerment`.`code_table_management` WHERE table_name = 'icbc_pos_code' AND foreign_relation_table_id IS NULL;"
    data = query_sql(pool, sql)  # 假设返回协程对象

    # 正确获取结果
    results = loop.run_until_complete(data)
    print(results)

    # 关闭事件循环
