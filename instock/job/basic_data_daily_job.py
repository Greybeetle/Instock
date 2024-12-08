#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/9'

"""
获取个股每日的行情数据
"""

import logging
import os.path
import sys
import pandas as pd

cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)

import instock.lib.run_template as runt
import instock.core.tablestructure as tbs
import instock.lib.database as mdb
import instock.core.stockfetch as stf
from instock.core.singleton_stock import stock_data


# 股票实时行情数据。
def save_nph_stock_spot_data(date):
    """
    获取股票行情数据
    :param date: 交易日期
    :return: None
    """
    try:
        data = stock_data().get_data(date)
        if data is None or len(data.index) == 0:
            return
        table_name = tbs.TABLE_CN_STOCK_SPOT['name']  # 每日股票数据表
        # 判断数据表是否存在
        if mdb.checkTableIsExist(table_name):
            count_sql = f"select count(1) FROM `{table_name}` where `date` = '{date}'"
            existed_count = mdb.executeSqlCount(count_sql)
            # 选择的日期的数据是否已入库
            if existed_count == data.shape[0]:
                return
            # 选择日期的数据未入库
            else:
                del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
                mdb.executeSql(del_sql)
                cols_type = None
                mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_SPOT['columns'])
            mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")

    except Exception as e:
        logging.error(f"basic_data_daily_job.save_stock_spot_data处理异常：{e}")


# 基金实时行情数据
def save_nph_etf_spot_data(date):
    """
    获取ETF基金行情数据
    :param date: 交易日期
    :return: None
    """
    try:
        data = stf.fetch_etfs(date)   # 从东方财富获取行情数据
        if data is None or len(data.index) == 0:
            return

        table_name = tbs.TABLE_CN_ETF_SPOT['name']   # 获取数据表名称
        # 判断数据表是否存在
        if mdb.checkTableIsExist(table_name):
            count_sql = f"select count(1) FROM `{table_name}` where `date` = '{date}'"
            existed_count = mdb.executeSqlCount(count_sql)
            # 选择的日期的数据是否已入库
            if existed_count == data.shape[0]:
                return
            # 选择日期的数据未入库
            else:
                del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
                mdb.executeSql(del_sql)
                cols_type = None
                mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_ETF_SPOT['columns'])
            mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")

    except Exception as e:
        logging.error(f"basic_data_daily_job.save_nph_etf_spot_data处理异常：{e}")


def main():
    """
    获取股票和ETF基金的行情基础数据
    :return:
    """
    runt.run_with_args(save_nph_stock_spot_data)  # 通过模板函数调用执行，模板函数内部判断数据是否已经保存到数据库中，如果已经保存，before为True，如果未保存，before为False
    runt.run_with_args(save_nph_etf_spot_data)


# main函数入口
if __name__ == '__main__':
    main()
