#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/9'

import logging
import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.types import NVARCHAR
from sqlalchemy import inspect


db_host = "localhost"  # 数据库服务主机
db_user = "root"  # 数据库访问用户
db_password = "1234qwer"  # 数据库访问密码
db_database = "instockdb"  # 数据库名称
db_port = 3306  # 数据库服务端口
db_charset = "utf8mb4"  # 数据库字符集

# 使用环境变量获得数据库,docker -e 传递
_db_host = os.environ.get('db_host')
if _db_host is not None:
    db_host = _db_host
_db_user = os.environ.get('db_user')
if _db_user is not None:
    db_user = _db_user
_db_password = os.environ.get('db_password')
if _db_password is not None:
    db_password = _db_password
_db_database = os.environ.get('db_database')
if _db_database is not None:
    db_database = _db_database
_db_port = os.environ.get('db_port')
if _db_port is not None:
    db_port = int(_db_port)

MYSQL_CONN_URL = "mysql+pymysql://%s:%s@%s:%s/%s?charset=%s" % (db_user, db_password, db_host, db_port, db_database, db_charset)
logging.info(f"数据库链接信息：{ MYSQL_CONN_URL}")

MYSQL_CONN_DBAPI = {'host': db_host, 'user': db_user, 'password': db_password, 'database': db_database, 'charset': db_charset, 'port': db_port, 'autocommit': True}

MYSQL_CONN_TORNDB = {'host': f'{db_host}:{str(db_port)}', 'user': db_user, 'password': db_password, 'database': db_database, 'charset': db_charset, 'max_idle_time': 3600, 'connect_timeout': 1000}


def engine():
    """
    创建数据库链接engine
    :return: engine
    """
    return create_engine(MYSQL_CONN_URL)


def engine_to_db(to_db):
    """
    创建数据库链接engine，区别在于修改保存数据的数据库名称，用于从一个数据库中向另一个数据库迁移数据表
    :param to_db:
    :return:
    """
    _engine = create_engine(MYSQL_CONN_URL.replace(f'/{db_database}?', f'/{to_db}?'))
    return _engine


def get_connection():
    """
    创建pymysql connection对象，DB Api -数据库连接对象connection
    :return: 返回connection对象
    """
    try:
        return pymysql.connect(**MYSQL_CONN_DBAPI)
    except Exception as e:
        logging.error(f"database.conn_not_cursor处理异常：{MYSQL_CONN_DBAPI}{e}")
    return None


def insert_db_from_df(data, table_name, cols_type, write_index, primary_keys, indexs=None):
    """
    定义通用方法函数，插入数据库表，并创建数据库主键，保证重跑数据的时候索引唯一。
    :param data: 待插入的数据
    :param table_name: 数据表名
    :param cols_type: 数据字段类型
    :param write_index: 写入数据表的索引
    :param primary_keys: 数据表主键
    :param indexs:
    :return: None
    """
    # 插入默认的数据库。
    insert_other_db_from_df(None, data, table_name, cols_type, write_index, primary_keys, indexs)


def insert_other_db_from_df(to_db, data, table_name, cols_type, write_index, primary_keys, indexs=None):
    """
    实际执行插入数据的方法，可以设定新的tb_db而实现将数据插入到其他数据库中
    :param to_db: 其他数据库名称，默认为None
    :param data: 待插入的数据
    :param table_name: 数据表名
    :param cols_type: 数据字段类型
    :param write_index: 写入数据表的索引
    :param primary_keys: 数据表主键
    :param indexs:
    :return: None
    """
    # 定义engine
    if to_db is None:
        engine_mysql = engine()
    else:
        engine_mysql = engine_to_db(to_db)
    # 使用 http://docs.sqlalchemy.org/en/latest/core/reflection.html
    # 使用检查检查数据库表是否有主键。
    ipt = inspect(engine_mysql)   # inspect()用于检测数据库连接对象的各类信息
    col_name_list = data.columns.tolist()
    # 如果有索引，把索引增加到varchar上面。
    if write_index:
        # 插入到第一个位置：
        col_name_list.insert(0, data.index.name)
    try:
        if cols_type is None:
            data.to_sql(name=table_name, con=engine_mysql, schema=to_db, if_exists='append',
                        index=write_index, )
        elif not cols_type:
            data.to_sql(name=table_name, con=engine_mysql, schema=to_db, if_exists='append',
                        dtype={col_name: NVARCHAR(255) for col_name in col_name_list}, index=write_index, )
        else:
            data.to_sql(name=table_name, con=engine_mysql, schema=to_db, if_exists='append',
                        dtype=cols_type, index=write_index, )
    except Exception as e:
        logging.error(f"database.insert_other_db_from_df处理异常：{table_name}表{e}")

    # 判断是否存在主键
    if not ipt.get_pk_constraint(table_name)['constrained_columns']:
        try:
            # 执行数据库插入数据。
            with get_connection() as conn:
                with conn.cursor() as db:
                    db.execute(f'ALTER TABLE `{table_name}` ADD PRIMARY KEY ({primary_keys});')
                    if indexs is not None:
                        for k in indexs:
                            db.execute(f'ALTER TABLE `{table_name}` ADD INDEX IN{k}({indexs[k]});')
        except Exception as e:
            logging.error(f"database.insert_other_db_from_df处理异常：{table_name}表{e}")


def update_db_from_df(data, table_name, where):
    """
    更新数据表中的数据
    :param data: 待更新的数据
    :param table_name: 数据表名
    :param where: 过滤条件
    :return: None
    """
    data = data.where(data.notnull(), None)
    update_string = f'UPDATE `{table_name}` set '
    where_string = ' where '
    cols = tuple(data.columns)
    with get_connection() as conn:
        with conn.cursor() as db:
            try:
                for row in data.values:
                    sql = update_string
                    sql_where = where_string
                    for index, col in enumerate(cols):
                        if col in where:
                            if len(sql_where) == len(where_string):
                                if type(row[index]) == str:
                                    sql_where = f'''{sql_where}`{col}` = '{row[index]}' '''
                                else:
                                    sql_where = f'''{sql_where}`{col}` = {row[index]} '''
                            else:
                                if type(row[index]) == str:
                                    sql_where = f'''{sql_where} and `{col}` = '{row[index]}' '''
                                else:
                                    sql_where = f'''{sql_where} and `{col}` = {row[index]} '''
                        else:
                            if type(row[index]) == str:
                                if row[index] is None or row[index] != row[index]:
                                    sql = f'''{sql}`{col}` = NULL, '''
                                else:
                                    sql = f'''{sql}`{col}` = '{row[index]}', '''
                            else:
                                if row[index] is None or row[index] != row[index]:
                                    sql = f'''{sql}`{col}` = NULL, '''
                                else:
                                    sql = f'''{sql}`{col}` = {row[index]}, '''
                    sql = f'{sql[:-2]}{sql_where}'
                    db.execute(sql)
            except Exception as e:
                logging.error(f"database.update_db_from_df处理异常：{sql}{e}")


def checkTableIsExist(tableName):
    """
    检查数据表是否存在
    :param tableName: 待检查的数据表名称
    :return: True or False
    """
    sql = """SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{0}'""".format(tableName.replace('\'', '\'\''))
    with get_connection() as conn:
        with conn.cursor() as db:
            db.execute(sql)
            if db.fetchone()[0] == 1:
                return True
    return False


def executeSql(sql, params=()):
    """
    增删改数据
    :param sql: 需要执行的sql语句
    :param params: 执行过程中的参数
    :return: None
    """
    with get_connection() as conn:
        with conn.cursor() as db:
            try:
                res = db.execute(sql)
            except Exception as e:
                logging.error(f"database.executeSql处理异常：{sql}{e}")


def executeSqlFetch(sql, params=()):
    """
    查询数据的函数
    :param sql: 需要查询的sql语句
    :param params: 参数
    :return:
    """
    with get_connection() as conn:
        with conn.cursor() as db:
            try:
                db.execute(sql, params)
                return db.fetchall()
            except Exception as e:
                logging.error(f"database.executeSqlFetch处理异常：{sql}{e}")
    return None


def executeSqlCount(sql, params=()):
    """
    计算数据表中的数量
    :param sql: 执行sql语句
    :param params: 参数
    :return: 计算的记录数据量
    """
    with get_connection() as conn:
        with conn.cursor() as db:
            try:
                db.execute(sql, params)
                result = db.fetchall()
                if len(result) == 1:
                    return int(result[0][0])
                else:
                    return 0
            except Exception as e:
                logging.error(f"database.select_count计算数量处理异常：{e}")
    return 0
