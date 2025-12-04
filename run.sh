#!/bin/bash

# 课程评价平台启动脚本

echo "正在安装依赖..."
pip3 install -r requirements.txt

echo "正在初始化数据库..."
python3 init_db.py

echo "启动应用..."
python3 app.py

