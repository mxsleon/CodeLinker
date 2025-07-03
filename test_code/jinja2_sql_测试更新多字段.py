from jinja2 import Environment, BaseLoader
from typing import Optional, Literal
from datetime import datetime

from db.db_config import db_settings


# 全局 SQL 环境实例
class SafeSQLEnvironment(Environment):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.update({
            'sql_identifier': self.sql_identifier_filter,
            'sql_value': self.sql_value_filter,
            'sql_expression': self.sql_expression_filter
        })

    @staticmethod
    def sql_identifier_filter(value):
        """处理 SQL 标识符（表名、列名）"""
        return f"{value}"

    @staticmethod
    def sql_value_filter(value):
        """处理 SQL 值 - 直接嵌入到 SQL 中"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f"'{str(value)}'"

    @staticmethod
    def sql_expression_filter(value):
        """处理 SQL 表达式（如 login_attempts + 1）"""
        return str(value)


# 全局 SQL 环境实例
SQL_ENV = SafeSQLEnvironment(loader=BaseLoader())


def render_sql_template(template_str, data):
    """渲染 SQL 模板并返回完整 SQL 语句"""
    template = SQL_ENV.from_string(template_str)
    return template.render(data)


def update_sql_update_user(
        id: str,
        is_active: Optional[bool] = None,
        last_login: Optional[datetime] = None,
        login_attempts: Literal['plus', 'reset', None] = None,
        locked_until: Optional[datetime] = None
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
    return render_sql_template(template_str, {
        "table_name": table_name,
        "update_fields": update_fields,
        "login_attempts_expr": login_attempts_expr,
        "id": id
    })
# 使用示例
if __name__ == "__main__":
    from datetime import datetime, timedelta
    # 示例 3: 登录尝试次数+1并锁定账户
    future_time = datetime.now() + timedelta(minutes=30)
    sql3 = update_sql_update_user(
        id="19f7adca-50d2-11f0-b677-08bfb83e31a7",
        login_attempts="plus",
        locked_until=future_time
    )
    print("\n示例3 - 登录尝试+1并锁定账户:")
    print(sql3)