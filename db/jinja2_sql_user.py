# -*- coding: UTF-8 -*-
"""
@File    ：api/admin_user/user_self_management.py
@Date    ：2025/7/4
@Author  ：mxsleon
@Website ：https://mxsleon.com
"""

from typing import Literal

from core.security import get_password_hash
from db.db_config import db_settings
from db.jinja2_env import render_sql_template
from schemas.user import RoleEnum, StatusEnum


def insert_into_new_user(username, password_hash, role, is_admin, is_active):
    """

    :param username:
    :param password_hash:
    :param role:
    :param is_admin:
    :param is_active:
    :return:
    """
    table_name = db_settings.USER_TABLE
    template_ = """
    INSERT INTO {{ table_name | sql_identifier }}  
    (username, password_hash, role, is_admin, is_active)
    VALUES 
    ({% if username %}{{ username | sql_value }}{% endif %}, 
    {% if password_hash %}{{ password_hash | sql_value }}{% endif %}, 
    {% if role %}{{ role | sql_value }}{% endif %}, 
    {% if is_admin %}{{ is_admin | sql_value }}{% endif %}, 
    {% if is_active %}{{ is_active | sql_value }}{% endif %});"""

    return render_sql_template(template_, {
        'username': username,
        'table_name': table_name,
        'password_hash': password_hash,
        'role': role,
        'is_admin': is_admin,
        'is_active': is_active,
    })

def get_user_info_sql(username,id =None,query_type: Literal["exact", "fuzzy"]= "exact"):
    """

    :param id: 传入查找的uuid
    :param username: 传入需查找的用户名
    :param query_type:
    :return: 返回sql语句
    """
    if query_type == "fuzzy":
        username =  f'%{username}%'

    table_name = db_settings.USER_TABLE
    template_ = """
SELECT `id`,`username`,`role`,`is_admin`,`is_active`,`last_login`,`login_attempts`,`locked_until`,`created_at`,`updated_at`
FROM  {{ table_name | sql_identifier }}  
WHERE 1 = 1
{% if id %}AND id = {{ id | sql_value }}{% endif %}
{% if username and  query_type == 'exact'%}AND username = {{ username | sql_value }}{% endif %}
{% if username and  query_type == 'fuzzy'%}AND username LIKE {{ username | sql_value }}{% endif %};
    """
    return render_sql_template(template_, {
        'id': id,
        'table_name': table_name,
        'username': username,
        'query_type': query_type,
    })

def get_user_info_sql_all(role:RoleEnum):
    """

    :param role:传入角色
    :return:
    """
    role_list = [i.value for i in role.get_roles_with_lower_or_equal_weight() ]
    role_list = tuple(role_list)
    table_name = db_settings.USER_TABLE
    template_ = """
SELECT `id`,`username`,`role`,`is_admin`,`is_active`,`last_login`,`login_attempts`,`locked_until`,`created_at`,`updated_at`
FROM  {{ table_name | sql_identifier }}  
WHERE 1 = 1
AND role in {{ role_list | sql_expression }};
    """
    return render_sql_template(template_, {
        'table_name': table_name,
        'role_list':role_list
    })

def get_user_info_sql_other(username,role:RoleEnum,query_type: Literal["exact", "fuzzy"]= "exact"):
    """

    :param username:
    :param role:
    :param query_type:
    :return:
    """

    role_list = [i.value for i in role.get_roles_with_lower_or_equal_weight() ]
    role_list = tuple(role_list)
    if query_type == "fuzzy":
        username =  f'%{username}%'
    table_name = db_settings.USER_TABLE
    template_ = """
SELECT `id`,`username`,`role`,`is_admin`,`is_active`,`last_login`,`login_attempts`,`locked_until`,`created_at`,`updated_at`
FROM  {{ table_name | sql_identifier }}  
WHERE role in {{ role_list | sql_expression }}
{% if username and  query_type == 'exact'%}AND username = {{ username | sql_value }}{% endif %}
{% if username and  query_type == 'fuzzy'%}AND username LIKE {{ username | sql_value }}{% endif %};
    """
    return render_sql_template(template_, {
        'table_name': table_name,
        'role_list':role_list,
        'username':username,
        'query_type':query_type
    })



def update_user_info_sql(
        id: str,
        username: str,
        role: RoleEnum = None,
        is_active: StatusEnum = None,
        clean_locked: bool = False
):
    """

    :param id:
    :param username:
    :param role:
    :param is_active:
    :param clean_locked:
    :return:
    """
    table_name = db_settings.USER_TABLE
    template = """
UPDATE {{ table_name | sql_identifier }}
SET
    {% if role is not none %}
    `role` = {{ role.value | sql_value }},
    `is_admin` = {{ 1 if role.weight > 1 else 0 | sql_value }},
    {% endif %}
    {% if is_active is not none %}
    `is_active` = {{ is_active.value | sql_value }},
    {% endif %}
    {% if clean_locked %}
    `login_attempts` = 0,
    `locked_until` = NULL,
    {% endif %}
    updated_at = NOW()
WHERE
    id = {{ id | sql_value }}
    AND username = {{ username | sql_value }};
"""
    context = {
        'table_name': table_name,
        'id': id,
        'username': username,
        'role': role,
        'is_active': is_active,
        'clean_locked': clean_locked
    }

    # 渲染 SQL 模板
    return render_sql_template(template, context)



def update_user_forget_password_sql(
        id: str,
        username: str,
        clean_locked: bool = False
):
    """

    :param id:
    :param username:
    :param clean_locked:
    :return:
    """
    password_hash = get_password_hash(username)
    table_name = db_settings.USER_TABLE
    template = """
UPDATE {{ table_name | sql_identifier }}
SET
    password_hash =  {{ password_hash | sql_value }},
    {% if clean_locked %}
    `login_attempts` = 0,
    `locked_until` = NULL,
    {% endif %}
    updated_at = NOW()
WHERE
    id = {{ id | sql_value }}
    AND username = {{ username | sql_value }};
"""
    context = {
        'table_name': table_name,
        'id': id,
        'username': username,
        'password_hash': password_hash,
        'clean_locked': clean_locked
    }

    # 渲染 SQL 模板
    return render_sql_template(template, context)


def count_username_sql(username: str):
    """

    :param username:传入用户名，拼接查询用户名个数sql
    :return:返回查询用户名个数的sql
    """
    table_name = db_settings.USER_TABLE

    template = """
SELECT COUNT(1) as user_num
FROM {{ table_name | sql_identifier }}
WHERE username = {{ username | sql_value }};"""

    context = {
        'table_name': table_name,
        'username': username
    }
    # 渲染 SQL 模板
    return render_sql_template(template, context)


def update_self_management_sql(
        id: str,
        new_username : str = None,
        new_password:str = None,
):
    """

    :param id:
    :param new_username:
    :param new_password:
    :return:
    """
    table_name = db_settings.USER_TABLE

    template = """
UPDATE {{ table_name | sql_identifier }}
SET
    {% if new_username %}username =  {{ new_username | sql_value }},{% endif %}
    {% if new_password %}password_hash =  {{ new_password | sql_value }},{% endif %}
    updated_at = NOW()
WHERE
    id = {{ id | sql_value }};"""

    context = {
        'table_name': table_name,
        'id': id,
        'new_username': new_username,
        'new_password':new_password
    }

    # 渲染 SQL 模板
    return render_sql_template(template, context)



if __name__ == "__main__":
    sql = update_self_management_sql(id='19f7adca-50d2-11f0-b677-08bfb83e31a7',new_username='123')
    print(sql)
