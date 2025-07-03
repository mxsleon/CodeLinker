from jinjasql import JinjaSql
j = JinjaSql()

def get_complete_sql(query, params):
    """将参数化查询转换为完整 SQL 语句"""
    # 确保 params 是元组或列表
    if not isinstance(params, (tuple, list)):
        params = [params]

    # 处理每个参数
    param_values = []
    for param in params:
        if param is None:
            param_values.append("NULL")
        elif isinstance(param, (int, float)):
            param_values.append(str(param))
        elif isinstance(param, bool):
            param_values.append("TRUE" if param else "FALSE")
        else:
            # 字符串类型 - 转义单引号
            escaped = str(param).replace("'", "''")
            param_values.append(f"'{escaped}'")

    # 替换查询中的占位符
    return query % tuple(param_values)

# 修改模板：使用条件语句
template = """
SELECT * FROM users 
WHERE 1=1
{% if 'city_name' in data %}AND city = {{ data.city_name }}{% endif %}
{% if 'age' in data %}AND age > {{ data.age }}{% endif %}
"""

# 测试数据 - 包含 city_name
data_with_city = {"city_name": 0, "age": 30}
query, params = j.prepare_query(template, {"data": data_with_city})
print("=== 包含 city_name ===")
print("查询:", query)
print("参数:", params)
# 使用示例
complete_sql = get_complete_sql(query, params)
print("完整 SQL:", complete_sql)


# 测试数据 - 不包含 city_name
data_without_city = {"age": 30}
query, params = j.prepare_query(template, {"data": data_without_city})
print("\n=== 不包含 city_name ===")
print("查询:", query)
print("参数:", params)
# 使用示例
complete_sql = get_complete_sql(query, params)
print("完整 SQL:", complete_sql)




