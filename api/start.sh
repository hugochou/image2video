#!/bin/bash

# 确保在脚本所在目录运行
cd "$(dirname "$0")"

# 创建必要的目录
mkdir -p api_uploads api_output api_temp logs

# 加载虚拟环境（如果存在）
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# 启动API服务器，使用端口8000
python api_server.py --port 8000 