FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY ../requirements.txt /app/requirements.txt
COPY ../src /app/src
COPY ./api_server.py /app/api/api_server.py

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/api/api_uploads /app/api/api_output /app/api/api_temp /app/api/logs

# 暴露端口
EXPOSE 5000

# 工作目录切换到api文件夹
WORKDIR /app/api

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "api_server:app"] 