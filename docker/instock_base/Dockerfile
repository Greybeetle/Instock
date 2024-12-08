FROM python:3.11-rc-slim

MAINTAINER ghx
ENV LANG=zh_CN.UTF-8
ENV LC_CTYPE=zh_CN.UTF-8
ENV LC_ALL=C
ENV PYTHONPATH=/data/InStock

WORKDIR /data/InStock
COPY ./docker/instock_base/ta-lib-0.4.0-src.tar.gz /data/InStock/ta-lib-0.4.0-src.tar.gz
COPY ./requirements.txt /data/InStock/requirements.txt


RUN sed -i "s@http://\(deb\|security\).debian.org@https://mirrors.aliyun.com@g" /etc/apt/sources.list && \
    echo  "[global]\n\
index-url = https://pypi.tuna.tsinghua.edu.cn/simple\n\
trusted-host = pypi.tuna.tsinghua.edu.cn" > /etc/pip.conf && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apt-get update && \
    apt-get install -y pkg-config cron gcc make python3-dev default-libmysqlclient-dev curl && \
    pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt && \
#    curl -SL https://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz | tar -xzC . && \
    cd /data/InStock/ && \
    tar -zxf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/  && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    pip install TA-Lib && \
    rm -rf ta-lib* && \
    apt-get --purge remove -y gcc make python3-dev default-libmysqlclient-dev curl && \
    rm -rf /root/.cache/* && apt-get clean && apt-get autoremove -y