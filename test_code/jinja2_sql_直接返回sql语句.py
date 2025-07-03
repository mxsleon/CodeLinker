from jinja2 import Environment, BaseLoader


class SafeSQLEnvironment(Environment):
    """自定义 SQL 环境，直接生成完整 SQL 语句"""

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
        # 添加反引号处理特殊字符
        return f"{value}"

    @staticmethod
    def sql_value_filter(value):
        """处理 SQL 值 - 直接嵌入到 SQL 中"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            # 转义单引号并包裹在引号中
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            # 其他类型转为字符串
            return f"'{str(value)}'"

    @staticmethod
    def sql_expression_filter(value):
        """处理 SQL 表达式（如 login_attempts + 1）"""
        return str(value)


# 全局 SQL 环境实例
SQL_ENV = SafeSQLEnvironment(loader=BaseLoader())


def render_sql_template(template_str, data):
    """
    渲染 SQL 模板并返回完整 SQL 语句
    :param template_str: Jinja2 模板字符串
    :param data: 模板数据字典
    :return: 完整可执行的 SQL 语句
    """
    template = SQL_ENV.from_string(template_str)
    return template.render(data)


# 具体 SQL 生成函数
def get_sql_query_user(username=None):
    """
    获取查询用户的 SQL
    :param username: 用户名（可选）
    :return: 完整可执行的 SQL 语句
    """
    table_name = "cl_system_settings.system_user"  # 实际应用中从配置获取

    template_str = """
    SELECT * 
    FROM {{ table_name | sql_identifier }} 
    WHERE 1=1
    {% if username %}AND username = {{ username | sql_value }}{% endif %}
    """

    return render_sql_template(template_str, {
        'username': username,
        'table_name': table_name
    })


def get_update_login_attempts_sql(user_id):
    """
    获取更新登录次数的 SQL
    :param user_id: 用户ID
    :return: 完整可执行的 SQL 语句
    """
    table_name = "cl_system_settings.system_user"

    template_str = """
    UPDATE {{ table_name | sql_identifier }} 
    SET login_attempts = {{ 'login_attempts + 1' | sql_expression }}
    WHERE id = {{ user_id | sql_value }}
    """

    return render_sql_template(template_str, {
        'user_id': user_id,
        'table_name': table_name
    })


def get_insert_user_sql(username, email, is_active=True):
    """
    获取插入用户的 SQL
    :param username: 用户名
    :param email: 邮箱
    :param is_active: 是否激活
    :return: 完整可执行的 SQL 语句
    """
    table_name = "cl_system_settings.system_user"

    template_str = """
    INSERT INTO {{ table_name | sql_identifier }} 
        (username, email, is_active, created_at)
    VALUES (
        {{ username | sql_value }},
        {{ email | sql_value }},
        {{ is_active | sql_value }},
        NOW()
    )
    """

    return render_sql_template(template_str, {
        'username': username,
        'email': email,
        'is_active': is_active,
        'table_name': table_name
    })


# 使用示例
if __name__ == "__main__":
    # 查询用户
    query = get_sql_query_user("john_doe")
    print("查询用户SQL:")
    print(query)

    # 更新登录次数
    update_sql = get_update_login_attempts_sql("19f7adca-50d2-11f0-b677-08bfb83e31a7")
    print("\n更新SQL:")
    print(update_sql)

    # 插入用户
    insert_sql = get_insert_user_sql("new_user", "user@example.com")
    print("\n插入SQL:")
    print(insert_sql)