#!/bin/bash

# 设置颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 确保在脚本所在目录运行
cd "$(dirname "$0")"

echo -e "${BLUE}开始部署Image2Video API服务...${NC}"

# 检查系统类型
if [ -f /etc/redhat-release ]; then
    # CentOS/RHEL系统
    echo -e "${YELLOW}检测到CentOS/RHEL系统${NC}"
    
    # 安装必要依赖
    echo -e "${GREEN}安装必要依赖...${NC}"
    sudo yum -y install python3 python3-pip git ffmpeg nginx

    # 安装virtualenv
    echo -e "${GREEN}安装virtualenv...${NC}"
    sudo pip3 install virtualenv
    
    # 配置Nginx
    echo -e "${GREEN}配置Nginx...${NC}"
    sudo mkdir -p /etc/nginx/conf.d
    sudo tee /etc/nginx/conf.d/image2video.conf > /dev/null << EOL
server {
    listen 80;
    server_name \$hostname;

    access_log /var/log/nginx/image2video-access.log;
    error_log /var/log/nginx/image2video-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加超时时间，视频处理可能需要较长时间
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 上传文件大小限制
        client_max_body_size 100M;
    }
}
EOL

    # 重启Nginx
    echo -e "${GREEN}重启Nginx...${NC}"
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    # 配置防火墙
    echo -e "${GREEN}配置防火墙...${NC}"
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload

elif [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    echo -e "${YELLOW}检测到Debian/Ubuntu系统${NC}"
    
    # 安装必要依赖
    echo -e "${GREEN}安装必要依赖...${NC}"
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git ffmpeg nginx
    
    # 配置Nginx
    echo -e "${GREEN}配置Nginx...${NC}"
    sudo tee /etc/nginx/sites-available/image2video > /dev/null << EOL
server {
    listen 80;
    server_name \$hostname;

    access_log /var/log/nginx/image2video-access.log;
    error_log /var/log/nginx/image2video-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加超时时间，视频处理可能需要较长时间
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 上传文件大小限制
        client_max_body_size 100M;
    }
}
EOL

    # 启用配置
    sudo ln -sf /etc/nginx/sites-available/image2video /etc/nginx/sites-enabled/
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    # 配置防火墙（如果有）
    if command -v ufw > /dev/null; then
        echo -e "${GREEN}配置防火墙...${NC}"
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
    fi
    
else
    echo -e "${RED}未检测到支持的操作系统${NC}"
    exit 1
fi

# 创建虚拟环境
echo -e "${GREEN}创建Python虚拟环境...${NC}"
cd ..
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
cd api

# 创建必要的目录
echo -e "${GREEN}创建必要的目录...${NC}"
mkdir -p api_uploads api_output api_temp logs

# 创建systemd服务文件
echo -e "${GREEN}创建systemd服务文件...${NC}"
sudo tee /etc/systemd/system/image2video.service > /dev/null << EOL
[Unit]
Description=Image2Video API Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/../venv/bin/python $(pwd)/api_server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# 启动服务
echo -e "${GREEN}启动服务...${NC}"
sudo systemctl daemon-reload
sudo systemctl start image2video
sudo systemctl enable image2video

# 添加定时任务
echo -e "${GREEN}添加定时清理任务...${NC}"
(crontab -l 2>/dev/null; echo "0 3 * * * $(pwd)/cleanup.sh >> $(pwd)/logs/cleanup.log 2>&1") | crontab -

# 显示服务状态
echo -e "${GREEN}服务状态：${NC}"
sudo systemctl status image2video

# 获取服务器IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo -e "${GREEN}部署完成!${NC}"
echo -e "${YELLOW}API服务地址: http://$SERVER_IP${NC}"
echo -e "${YELLOW}Coze插件URL: http://$SERVER_IP${NC}"
echo -e "${YELLOW}图片转视频API路径: /api/image2video${NC}"
echo -e "${YELLOW}视频合成API路径: /api/merge-videos${NC}"
echo -e "${YELLOW}健康检查API路径: /health${NC}"
echo -e "${BLUE}日志查看: tail -f logs/api.log${NC}"
echo -e "${BLUE}服务控制: sudo systemctl {start|stop|restart|status} image2video${NC}" 