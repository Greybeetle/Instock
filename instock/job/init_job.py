#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/10'

import logging
import pymysql
import os.path
import sys

cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
import instock.lib.database as mdb


def create_new_database():
    """
    创建新数据库
    :return:
    """
    _MYSQL_CONN_DBAPI = mdb.MYSQL_CONN_DBAPI.copy()
    _MYSQL_CONN_DBAPI['database'] = "mysql"
    with pymysql.connect(**_MYSQL_CONN_DBAPI) as conn:
        with conn.cursor() as db:
            try:
                create_sql = f"CREATE DATABASE IF NOT EXISTS `{mdb.db_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
                db.execute(create_sql)
                create_new_base_table()
            except Exception as e:
                logging.error(f"init_job.create_new_database处理异常：{e}")


def create_new_base_table():
    """
    创建基础表
    :return:
    """
    with pymysql.connect(**mdb.MYSQL_CONN_DBAPI) as conn:
        with conn.cursor() as db:
            create_table_sql = """CREATE TABLE IF NOT EXISTS `cn_stock_attention` (
                                  `datetime` datetime(0) NULL DEFAULT NULL, 
                                  `code` varchar(6) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
                                  PRIMARY KEY (`code`) USING BTREE,
                                  INDEX `INIX_DATETIME`(`datetime`) USING BTREE
                                  ) CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;"""
            db.execute(create_table_sql)


def check_database():
    """
    检查数据库是否存在
    :return:
    """
    with pymysql.connect(**mdb.MYSQL_CONN_DBAPI) as conn:
        with conn.cursor() as db:
            db.execute(" select 1 ")


def main():
    """
    程序执行主入口，先检查数据库是否存在，如果不存在则创建一个新的数据库，如果存在，则直接新建所有表格
    :return:
    """
    # 检查，如果执行 select 1 失败，说明数据库不存在，然后创建一个新的数据库。
    try:
        create_new_base_table()
    except Exception as e:
        logging.error("执行信息：数据库不存在，将创建。")
        # 检查数据库失败，
        create_new_database()
    # 执行数据初始化。


# main函数入口
if __name__ == '__main__':
    main()
