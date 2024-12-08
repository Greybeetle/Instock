chcp 65001
@echo off
cd %~dp0
cd ..
cd job
echo ------整体作业，支持批量作业------
echo 当前时间作业 python execute_daily_job.py
echo 1个时间作业 python execute_daily_job.py 2023-03-01
echo N个时间作业 python execute_daily_job.py 2023-03-01,2023-03-02
echo 区间作业 python execute_daily_job.py 2023-03-01 2023-03-21
echo ------单功能作业，除了创建数据库，其他都支持批量作业------
echo 创建数据库作业 python init_job.py
echo 基础数据实时作业 python basic_data_daily_job.py
echo 基础数据非实时作业 python basic_data_other_daily_job.py
echo 指标数据作业 python indicators_data_daily_job.py
echo K线形态作业 python klinepattern_data_daily_job.py
echo 策略数据作业 python strategy_data_daily_job.py
echo 回测数据 python backtest_data_daily_job.py
echo ------正在执行作业中，请等待------
pause
exit