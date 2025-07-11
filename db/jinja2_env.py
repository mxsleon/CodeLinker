from jinja2 import Environment, BaseLoader


class SafeSQLEnvironment(Environment):
    """自定义 SQL 环境，直接生成完整 SQL 语句"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters.update(
            {
                "sql_identifier": self.sql_identifier_filter,
                "sql_value": self.sql_value_filter,
                "sql_expression": self.sql_expression_filter,
            }
        )

    @staticmethod
    def sql_identifier_filter(value):
        """处理 SQL 标识符（表名、列名）"""
        # 添加反引号处理特殊字符,xian
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
