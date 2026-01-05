#!/bin/bash

# 课程评价平台启动脚本

echo "正在安装依赖..."
pip3 install -r requirements.txt

echo "正在迁移数据库..."
python3 manage.py migrate

echo "启动Django服务..."
python3 manage.py runserver 8000
