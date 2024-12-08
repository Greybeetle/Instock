#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'hosea'
__date__ = '2024/7/11 '

"""
全流程操作入口，实现从数据获取-额外数据计算-K线形态处理-动态选股-选股结果回测等全链条任务
"""

import time
import datetime
import concurrent.futures   # 多线程执行模块
import logging
import os.path
import sys

# 在项目运行时，临时将项目路径添加到环境变量
cpath_current = os.path.dirname(os.path.dirname(__file__))
cpath = os.path.abspath(os.path.join(cpath_current, os.pardir))
sys.path.append(cpath)
log_path = os.path.join(cpath_current, 'log')
if not os.path.exists(log_path):
    os.makedirs(log_path)
logging.basicConfig(format='%(asctime)s %(message)s', filename=os.path.join(log_path, 'stock_execute_job.log'))
logging.getLogger().setLevel(logging.INFO)

import init_job as bj   # 创建数据库
import basic_data_daily_job as hdj
import basic_data_other_daily_job as hdtj
import indicators_data_daily_job as gdj
import strategy_data_daily_job as sdj
import backtest_data_daily_job as bdj
import klinepattern_data_daily_job as kdj
# import sycn_databases_daily_job as sddj


def main():
    """
    程序主入口，实现所有任务顺序执行
    :return:
    """
    start = time.time()
    _start = datetime.datetime.now()
    logging.info("######## 任务执行时间: %s #######" % _start.strftime("%Y-%m-%d %H:%M:%S.%f"))
    bj.main()  # 创建数据库
    hdj.main()  # 获取股票与基金的基础数据
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(hdtj.main)   # 获取股票其它基础数据，如龙虎榜单，资金流向等数据
        executor.submit(gdj.main)    # 计算股票指标数据，如macd、kdj等，并根据买入、卖出条件筛选相关股票
        executor.submit(kdj.main)    # 计算股票的K线形态，如三只乌鸦、乌云压顶等等
        executor.submit(sdj.main)    # 根据不同的选股策略进行选股，后续如果需要自行设计选股策略，只需要修改该部分相关的函数
    bdj.main()  # 对不同选股策略选出的股票进行回测，用于每日验证策略的选股能力
    # sddj.main()   # 将本地数据库同步到云服务的数据库上
    logging.info("######## 完成任务, 使用时间: %s 秒 #######" % (time.time() - start))


# main函数入口
if __name__ == '__main__':
    main()
