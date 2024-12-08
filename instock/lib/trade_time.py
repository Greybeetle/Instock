#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/9 '

"""
计算股市交易日期与时间等，比如是否交易日，是否交易时间段等
"""

import datetime
from instock.core.singleton_trade_date import stock_trade_date


def is_trade_date(date=None):
    """
    判断当前日期是否开盘
    """
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return False
    if date in trade_date:
        return True
    else:
        return False


def get_previous_trade_date(date):
    """
    获取当前日期的前一个交易日期
    """
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return date
    tmp_date = date
    while True:
        tmp_date += datetime.timedelta(days=-1)
        if tmp_date in trade_date:
            break
    return tmp_date


def get_next_trade_date(date):
    """
    获取当前交易日的下一个交易日期
    """
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return date
    tmp_date = date
    while True:
        tmp_date += datetime.timedelta(days=1)
        if tmp_date in trade_date:
            break
    return tmp_date


OPEN_TIME = (
    (datetime.time(9, 15, 0), datetime.time(11, 30, 0)),
    (datetime.time(13, 0, 0), datetime.time(15, 0, 0)),
)


def is_tradetime(now_time):
    """
    判断是否是交易时间，A股交易日期为19:15:00-11:30:00和13:00:00-15:00:00
    """
    now = now_time.time()
    for begin, end in OPEN_TIME:
        if begin <= now < end:
            return True
    else:
        return False


PAUSE_TIME = (
    (datetime.time(11, 30, 0), datetime.time(12, 59, 30)),
)


def is_pause(now_time):
    """
    判断是否为当日暂定交易时间，午盘休市时间11:30:00-12:59:30
    """
    now = now_time.time()
    for b, e in PAUSE_TIME:
        if b <= now < e:
            return True


CONTINUE_TIME = (
    (datetime.time(12, 59, 30), datetime.time(13, 0, 0)),
)


def is_continue(now_time):
    """
    判断是否继续交易时间，即12:59:30-13:00:00
    """
    now = now_time.time()
    for b, e in CONTINUE_TIME:
        if b <= now < e:
            return True
    return False


CLOSE_TIME = (
    datetime.time(15, 0, 0),
)


def is_closing(now_time, start=datetime.time(14, 54, 30)):
    """
    判断是否尾盘集合竞价，即14:54:30开始进入集合竞价阶段
    """
    now = now_time.time()
    for close in CLOSE_TIME:
        if start <= now < close:
            return True
    return False


def is_close(now_time):
    """
    判断是否闭市，即15:00:00
    """
    now = now_time.time()
    for close in CLOSE_TIME:
        if now >= close:
            return True
    return False


def is_open(now_time):
    """
    判断是否正式开市，即9:30:00
    """
    now = now_time.time()
    if now >= datetime.time(9, 30, 0):
        return True
    return False


def get_trade_hist_interval(date):
    """
    获取三年前的交易日期及是否开盘
    """
    tmp_year, tmp_month, tmp_day = date.split("-")
    date_end = datetime.datetime(int(tmp_year), int(tmp_month), int(tmp_day))
    date_start = (date_end + datetime.timedelta(days=-(365 * 3))).strftime("%Y%m%d")

    now_time = datetime.datetime.now()
    now_date = now_time.date()
    is_trade_date_open_close_between = False
    if date_end.date() == now_date:
        if is_trade_date(now_date):
            if is_open(now_time) and not is_close(now_time):
                is_trade_date_open_close_between = True

    return date_start, not is_trade_date_open_close_between


def get_trade_date_last():
    """
    获取最新的交易日期，如果日期未开盘，那么获取最新的交易日期，返回交易日期和前一期的交易日期
    """
    now_time = datetime.datetime.now()
    run_date = now_time.date()
    run_date_nph = run_date
    if is_trade_date(run_date):
        if not is_close(now_time):
            run_date = get_previous_trade_date(run_date)
            if not is_open(now_time):
                run_date_nph = run_date
    else:
        run_date = get_previous_trade_date(run_date)
        run_date_nph = run_date
    return run_date, run_date_nph


def get_quarterly_report_date():
    """
    获取最新季报日期，如1季度季度结束日期为0331，则返回20240331
    """
    now_time = datetime.datetime.now()
    year = now_time.year
    month = now_time.month
    if 1 <= month <= 3:
        month_day = '1231'
    elif 4 <= month <= 6:
        month_day = '0331'
    elif 7 <= month <= 9:
        month_day = '0630'
    else:
        month_day = '0930'
    return f"{year}{month_day}"


def get_bonus_report_date():
    """
    获取最新分红日期
    """
    now_time = datetime.datetime.now()
    year = now_time.year
    month = now_time.month
    if 2 <= month <= 6:
        year -= 1
        month_day = '1231'
    elif 8 <= month <= 12:
        month_day = '0630'
    elif month == 7:
        if now_time.day > 25:
            month_day = '0630'
        else:
            year -= 1
            month_day = '1231'
    else:
        year -= 1
        if now_time.day > 25:
            month_day = '1231'
        else:
            month_day = '0630'
    return f"{year}{month_day}"
