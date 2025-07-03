from jinja2 import Environment, BaseLoader
import re


# 创建自定义环境
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
        # 在实际应用中，您可能需要添加反引号处理特殊字符
        # 例如：return f"`{value}`"
        return str(value)

    @staticmethod
    def sql_value_filter(value):
        """处理 SQL 值 - 标记为需要参数化"""
        # 使用唯一标识符作为占位符
        return f"<SQL_VALUE_{id(value)}>"

    @staticmethod
    def sql_expression_filter(value):
        """处理 SQL 表达式（如 login_attempts + 1）"""
        return str(value)


# SQL 模板渲染装饰器
def sql_template(func):
    """装饰器：自动渲染 Jinja2 模板并处理占位符"""

    def wrapper(*args, **kwargs):
        # 调用原始函数获取模板和数据
        result = func(*args, **kwargs)

        if isinstance(result, tuple) and len(result) == 2:
            template_str, data = result
        else:
            raise ValueError("Decorated function must return (template_str, data)")

        # 创建自定义环境
        env = SafeSQLEnvironment(loader=BaseLoader())
        template = env.from_string(template_str)

        # 渲染模板
        sql_with_placeholders = template.render(data)

        # 提取参数并替换占位符
        params = []
        pattern = r"<SQL_VALUE_(\d+)>"

        def replace_placeholder(match):
            placeholder_id = int(match.group(1))
            # 查找对应的值
            for value in data.values():
                if id(value) == placeholder_id:
                    params.append(value)
                    return "%s"
            raise ValueError(f"Placeholder {placeholder_id} not found in data")

        # 替换所有占位符
        final_sql = re.sub(pattern, replace_placeholder, sql_with_placeholders)

        return final_sql, params

    return wrapper


# 使用装饰器的示例
@sql_template
def get_sql_query_user(username=None):
    """
    :param username: 可选用户名
    :return: 返回 (template_str, data) 元组
    """
    table_name = "cl_system_settings.system_user"  # 实际应用中从配置获取

    template_str = """
    SELECT * FROM {{ table_name | sql_identifier }} 
    WHERE 1=1
    {% if username %}AND username = {{ username | sql_value }}{% endif %}
    """

    return template_str, {'username': username, 'table_name': table_name}


@sql_template
def get_update_login_attempts_sql(user_id):
    table_name = "cl_system_settings.system_user"

    template_str = """
    UPDATE {{ table_name | sql_identifier }} 
    SET
        {% if login_attempts %}login_attempts = {{ 'login_attempts + 1' | sql_expression }}{% endif %}
    WHERE id = {{ user_id | sql_value }}
    """

    return template_str, {'user_id': user_id, 'table_name': table_name,'login_attempts':'123'}


# 使用示例
if __name__ == "__main__":
    # 查询用户
    query, params = get_sql_query_user("john_doe")
    print("查询用户SQL:")
    print(query)
    print("参数:", params)

    # 更新登录次数
    update_sql, update_params = get_update_login_attempts_sql("19f7adca-50d2-11f0-b677-08bfb83e31a7")
    print("\n更新SQL:")
    print(update_sql)
    print("参数:", update_params)