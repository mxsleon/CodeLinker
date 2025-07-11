# db/jinja2_sql_auth.py

from datetime import datetime
from typing import Optional, Literal
from db.db_config import db_settings
from db.jinja2_env import render_sql_template


def get_sql_query_user(username):
    """
    :param username: 传入用户字符串
    :return: 返回querysql,params元祖
    """

    table_name = db_settings.USER_TABLE
    template_ = """
        SELECT * FROM {{ table_name | sql_identifier }} 
        WHERE 1=1
        {% if username %}AND username = {{ username | sql_value }}{% endif %}
        """

    return render_sql_template(
        template_, {"username": username, "table_name": table_name}
    )


def update_sql_update_user(
    id: str,
    is_active: Optional[bool] = None,
    last_login: Optional[datetime] = None,
    login_attempts: Literal["plus", "reset", None] = None,
    locked_until: Optional[datetime] = None,
) -> str:
    """
    更新用户信息并返回完整 SQL 语句

    :param id: 用户ID
    :param is_active: 账户激活状态
    :param last_login: 最后登录时间
    :param login_attempts:
        - None: 不改变尝试登录次数
        - "plus": 登录尝试次数+1
        - "reset": 重置登录尝试次数为0
    :param locked_until: 账户锁定时间
    :return: 完整可执行的 SQL 语句
    """
    table_name = db_settings.USER_TABLE

    # 准备更新字段
    update_fields = {}

    if is_active is not None:
        update_fields["is_active"] = is_active

    if last_login is not None:
        update_fields["last_login"] = last_login

    if locked_until is not None:
        update_fields["locked_until"] = locked_until

    # 处理登录尝试次数的特殊逻辑
    login_attempts_expr = None
    if login_attempts == "plus":
        login_attempts_expr = "login_attempts = login_attempts + 1"
    elif login_attempts == "reset":
        login_attempts_expr = "login_attempts = 0"

    # 构建模板 - 修复逗号问题
    template_str = """
    UPDATE {{ table_name | sql_identifier }} 
    SET
        {% if update_fields or login_attempts_expr %}
            {% set first = true %}
            {% for field, value in update_fields.items() -%}
                {% if not first %},{% endif %}{% set first = false %}
                {{ field | sql_identifier }} = {{ value | sql_value }}
            {%- endfor %}
            {% if login_attempts_expr %}
                {% if update_fields %},{% endif %}
                {{ login_attempts_expr }}
            {% endif %}
        {% else %}
            id = id 
        {% endif %}
    WHERE id = {{ id | sql_value }}
    """

    # 渲染并返回 SQL
    return render_sql_template(
        template_str,
        {
            "table_name": table_name,
            "update_fields": update_fields,
            "login_attempts_expr": login_attempts_expr,
            "id": id,
        },
    )


if __name__ == "__main__":
    print(get_sql_query_user(username="123"))
