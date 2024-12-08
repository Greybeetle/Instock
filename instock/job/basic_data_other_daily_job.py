#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/10 '

"""
获取股票其他行情数据，包括每日股票龙虎榜、每日股票大宗交易、每日股票资金流向、每日行业资金流向、每日股票分红数据，并且根据龙虎榜单数据进行基本面选股
"""

import logging
import concurrent.futures
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


# 获取每日股票龙虎榜数据
def save_nph_stock_top_data(date, before=False):
    """
    获取每日股票龙虎榜数据
    :param date: 日期
    :param before:
    :return:
    """
    if before:
        return
    try:
        data = stf.fetch_stock_top_data(date)
        if data is None or len(data.index) == 0:
            return
        table_name = tbs.TABLE_CN_STOCK_TOP['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_TOP['columns'])
        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.save_stock_top_data处理异常：{e}")
    stock_spot_buy(date)


# 获取每日股票大宗交易数据
def save_stock_blocktrade_data(date):
    """
    获取每日股票大宗交易数据
    :param date:
    :return:
    """
    try:
        data = stf.fetch_stock_blocktrade_data(date)
        if data is None or len(data.index) == 0:
            return

        table_name = tbs.TABLE_CN_STOCK_BLOCKTRADE['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_BLOCKTRADE['columns'])

        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.save_stock_blocktrade_data处理异常：{e}")


# 获取每日股票资金流向数据
def save_nph_stock_fund_flow_data(date, before=False):
    """
    获取每日股票资金流向数据
    :param date:
    :param before:
    :return:
    """
    if before:
        return

    try:
        times = tuple(range(4))
        results = run_check_stock_fund_flow(times)
        if results is None:
            return

        for t in times:
            if t == 0:
                data = results.get(t)
            else:
                r = results.get(t)
                if r is not None:
                    r.drop(columns=['name', 'new_price'], inplace=True)
                    data = pd.merge(data, r, on=['code'], how='left')

        if data is None or len(data.index) == 0:
            return

        data.insert(0, 'date', date.strftime("%Y-%m-%d"))

        table_name = tbs.TABLE_CN_STOCK_FUND_FLOW['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_FUND_FLOW['columns'])

        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.save_nph_stock_fund_flow_data处理异常：{e}")


# 对个股资金流向数据进行补充
def run_check_stock_fund_flow(times):
    """
    对资金流向数据进行补充计算，原始获取的资金流向数据只有当日的，此方法用于扩充近3日资金流向、近5日资金流向以及近10日资金流向动态
    :param times: 次数，因为要保存当日、近3日、近5日以及近10日的资金流向，所以times设置为4，通过参数传递过来的
    :return:
    """
    data = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(times)) as executor:
            future_to_data = {executor.submit(stf.fetch_stocks_fund_flow, k): k for k in times}
            for future in concurrent.futures.as_completed(future_to_data):
                _time = future_to_data[future]
                try:
                    _data_ = future.result()
                    if _data_ is not None:
                        data[_time] = _data_
                except Exception as e:
                    logging.error(f"basic_data_other_daily_job.run_check_stock_fund_flow处理异常：代码{e}")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.run_check_stock_fund_flow处理异常：{e}")
    if not data:
        return None
    else:
        return data


# 获取每日行业资金流向数据，内部调用stock_sector_fund_flow_data方法，也可以两者合并
def save_nph_stock_sector_fund_flow_data(date, before=False):
    """
    获取每日行业资金流向数据，内部调用stock_sector_fund_flow_data方法，也可以两者合并
    :param date:
    :param before:
    :return:
    """
    if before:
        return

    times = tuple(range(2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(times)) as executor:
        {executor.submit(stock_sector_fund_flow_data, date, k): k for k in times}


# 获取并保存每日行业资金流向数据，为了可读性，将其从save_nph_stock_sector_fund_flow_data方法中剥离出来
def stock_sector_fund_flow_data(date, index_sector):
    """
    获取并保存每日行业资金流向数据，为了可读性，将其从save_nph_stock_sector_fund_flow_data方法中剥离出来
    :param date:
    :param index_sector:
    :return:
    """
    try:
        times = tuple(range(3))
        results = run_check_stock_sector_fund_flow(index_sector, times)
        if results is None:
            return

        for t in times:
            if t == 0:
                data = results.get(t)
            else:
                r = results.get(t)
                if r is not None:
                    data = pd.merge(data, r, on=['name'], how='left')

        if data is None or len(data.index) == 0:
            return

        data.insert(0, 'date', date.strftime("%Y-%m-%d"))

        if index_sector == 0:
            tbs_table = tbs.TABLE_CN_STOCK_FUND_FLOW_INDUSTRY
        else:
            tbs_table = tbs.TABLE_CN_STOCK_FUND_FLOW_CONCEPT
        table_name = tbs_table['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs_table['columns'])

        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`name`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.stock_sector_fund_flow_data处理异常：{e}")


# 对行业资金流向数据进行补充
def run_check_stock_sector_fund_flow(index_sector, times):
    """
    对资金流向数据进行补充计算，原始获取的资金流向数据只有当日的，此方法用于扩充近3日资金流向、近5日资金流向以及近10日资金流向动态
    :param index_sector: 行业编号
    :param times: 对资金流向数据进行补充计算，原始获取的资金流向数据只有当日的，此方法用于扩充近3日资金流向、近5日资金流向以及近10日资金流向动态
    :return:
    """
    data = {}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(times)) as executor:
            future_to_data = {executor.submit(stf.fetch_stocks_sector_fund_flow, index_sector, k): k for k in times}
            for future in concurrent.futures.as_completed(future_to_data):
                _time = future_to_data[future]
                try:
                    _data_ = future.result()
                    if _data_ is not None:
                        data[_time] = _data_
                except Exception as e:
                    logging.error(f"basic_data_other_daily_job.run_check_stock_sector_fund_flow处理异常：代码{e}")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.run_check_stock_sector_fund_flow处理异常：{e}")
    if not data:
        return None
    else:
        return data


# 获取每日股票分红配送数据
def save_nph_stock_bonus(date, before=False):
    """
    获取每日股票分红配送数据
    :param date:
    :param before:
    :return:
    """
    if before:
        return

    try:
        data = stf.fetch_stocks_bonus(date)
        if data is None or len(data.index) == 0:
            return

        table_name = tbs.TABLE_CN_STOCK_BONUS['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_BONUS['columns'])
        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.save_nph_stock_bonus处理异常：{e}")


# 基本面选股函数
def stock_spot_buy(date):
    """
    基本面选股函数，筛选0<市盈率TTM<=20、市净率<=10、加权净资产收益率>=15的股票
    :param date:
    :return:
    """
    try:
        _table_name = tbs.TABLE_CN_STOCK_SPOT['name']
        if not mdb.checkTableIsExist(_table_name):
            return

        sql = f'''SELECT * FROM `{_table_name}` WHERE `date` = '{date}' and 
                `pe9` > 0 and `pe9` <= 20 and `pbnewmrq` <= 10 and `roe_weight` >= 15'''
        data = pd.read_sql(sql=sql, con=mdb.engine())
        data = data.drop_duplicates(subset="code", keep="last")
        if len(data.index) == 0:
            return

        table_name = tbs.TABLE_CN_STOCK_SPOT_BUY['name']
        # 删除老数据。
        if mdb.checkTableIsExist(table_name):
            del_sql = f"DELETE FROM `{table_name}` where `date` = '{date}'"
            mdb.executeSql(del_sql)
            cols_type = None
        else:
            cols_type = tbs.get_field_types(tbs.TABLE_CN_STOCK_SPOT_BUY['columns'])

        mdb.insert_db_from_df(data, table_name, cols_type, False, "`date`,`code`")
    except Exception as e:
        logging.error(f"basic_data_other_daily_job.stock_spot_buy处理异常：{e}")


def main():
    """
    获取每日行情数据的主函数，主要是获取龙虎榜单、大宗交易、分红、资金流向等数据
    :return:
    """
    runt.run_with_args(save_nph_stock_top_data)   # 获取龙虎榜单数据并根据基本面选股
    runt.run_with_args(save_stock_blocktrade_data)  # 获取每日大宗交易数据
    runt.run_with_args(save_nph_stock_bonus)   # 获取股票每日分红配送数据
    runt.run_with_args(save_nph_stock_fund_flow_data)  # 获取股票每日资金流向数据
    runt.run_with_args(save_nph_stock_sector_fund_flow_data)   # 获取行业板块和概念板块每日资金流向数据


# main函数入口
if __name__ == '__main__':
    main()
