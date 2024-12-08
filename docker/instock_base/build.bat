@echo off
REM 切换到当前目录的上两级目录，注意Windows下的目录分隔符是反斜杠，且命令稍有不同
cd ..\..
REM 设置Docker镜像名称变量
set DOCKER_NAME=instock_base
REM 设置Docker镜像标签变量
set TAG=latest

REM 输出即将执行的构建Docker镜像的命令（仅作展示，实际不执行构建），注意命令格式和Shell中的略有区别
echo docker build -f docker\instock_base\Dockerfile -t %DOCKER_NAME%:%TAG% .

REM 执行构建Docker镜像的命令
docker build -f docker\instock_base\Dockerfile -t %DOCKER_NAME%:%TAG% .
