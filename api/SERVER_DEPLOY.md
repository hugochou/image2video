# 服务器部署指南

本文档提供了在服务器上部署Image2Video API服务的步骤指南，包括一键部署和手动部署两种方式。

## 一、一键部署（推荐）

我们提供了一键部署脚本，可以自动完成所有配置步骤：

```bash
# 登录到服务器后
cd /home/your-username  # 切换到你的用户目录

# 下载项目
git clone https://your-repository-url/image2video.git
cd image2video

# 运行部署脚本
cd api
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动：
1. 安装所有必要的依赖
2. 配置Nginx
3. 设置防火墙
4. 创建Python虚拟环境
5. 安装API服务所需的Python包
6. 配置systemd服务实现开机自启
7. 添加定时清理任务

脚本运行完成后，你会看到API服务的地址和Coze插件需要的URL信息。

## 二、系统要求

- Python 3.7+
- 至少2GB RAM
- 至少10GB可用磁盘空间（用于存储临时文件和生成的视频）
- 公网IP或域名（用于Coze调用）

## 三、手动部署步骤

如果一键部署脚本不起作用，你可以按照以下步骤手动部署：

### 1. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git ffmpeg nginx
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip git ffmpeg nginx
```

### 2. 下载项目

```bash
git clone https://your-repository-url/image2video.git
cd image2video
```

### 3. 创建Python虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux
pip install -r requirements.txt
```

### 4. 配置API服务

```bash
cd api
mkdir -p api_uploads api_output api_temp logs
chmod +x start.sh cleanup.sh
```

### 5. 配置Nginx反向代理

根据你的系统类型，创建Nginx配置文件：

**CentOS/RHEL系统:**
```bash
sudo nano /etc/nginx/conf.d/image2video.conf
```

**Ubuntu/Debian系统:**
```bash
sudo nano /etc/nginx/sites-available/image2video
sudo ln -s /etc/nginx/sites-available/image2video /etc/nginx/sites-enabled/
```

配置文件内容：
```
server {
    listen 80;
    server_name 你的服务器IP;  # 或者你的域名

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间，视频处理可能需要较长时间
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 上传文件大小限制
        client_max_body_size 100M;
    }
}
```

重启Nginx：
```bash
sudo nginx -t  # 测试配置是否正确
sudo systemctl restart nginx
```

### 6. 配置SSL（可选但强烈推荐）

使用Let's Encrypt免费SSL:
```bash
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu/Debian
sudo certbot --nginx -d your-domain.com
```

### 7. 创建系统服务

```bash
sudo nano /etc/systemd/system/image2video.service
```

输入以下内容：
```
[Unit]
Description=Image2Video API Service
After=network.target

[Service]
User=你的用户名
WorkingDirectory=/home/你的用户名/image2video/api
ExecStart=/home/你的用户名/image2video/venv/bin/python /home/你的用户名/image2video/api/api_server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

或者如果使用Gunicorn（推荐用于生产环境）：
```
[Unit]
Description=Image2Video API Service
After=network.target

[Service]
User=你的用户名
WorkingDirectory=/home/你的用户名/image2video/api
ExecStart=/home/你的用户名/image2video/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 api_server:app
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start image2video
sudo systemctl enable image2video  # 设置开机自启
```

### 8. 设置定时清理

添加定时任务，每天清理旧文件：
```bash
(crontab -l 2>/dev/null; echo "0 3 * * * /home/你的用户名/image2video/api/cleanup.sh >> /home/你的用户名/image2video/api/logs/cleanup.log 2>&1") | crontab -
```

## 四、验证部署

### 测试API服务

```bash
curl http://localhost:8000/health
```

如果服务正常，你会看到类似以下响应：
```json
{"message":"Image2Video API服务正常运行","status":"ok"}
```

### 使用测试脚本

API目录中包含了测试脚本，可以用来验证API功能：

```bash
cd /home/你的用户名/image2video/api
python test_api.py --api-url http://localhost:8000 --help  # 查看帮助
python test_api.py --api-url http://localhost:8000  # 测试健康检查
```

## 五、Coze插件配置

### 创建HTTP Service Plugin

1. 进入Coze个人空间-插件
2. 点击"创建插件"
3. 选择创建方式为"HTTP Service Plugin"
4. 插件URL设置为您的服务器URL: `https://your-domain.com`或`http://your-server-ip`
5. 点击创建

### 配置图片转视频工具

1. 在插件中点击"创建工具"
2. 填写基本信息:
   - 工具名称: "图片转视频"
   - 工具描述: "将图片转换为带有动画效果的视频"
   - 工具路径: `/api/image2video`
   - 请求方式: `POST`

3. 配置输入参数:
   - 参数名称: `image_url`, 描述: "图片URL", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `audio_url`, 描述: "音频URL(可选)", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `animation_type`, 描述: "动画类型", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `animation_curve`, 描述: "动画曲线", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `duration`, 描述: "视频时长(秒)", 类型: `NUMBER`, 传入方法: `JSON`

4. 配置输出参数:
   - 参数名称: `status`, 描述: "处理状态", 类型: `STRING`
   - 参数名称: `video_url`, 描述: "生成的视频URL", 类型: `STRING`
   - 参数名称: `error`, 描述: "错误信息", 类型: `STRING`

### 配置视频合成工具

1. 在插件中点击"创建工具"
2. 填写基本信息:
   - 工具名称: "视频合成"
   - 工具描述: "将多个视频合成为一个视频"
   - 工具路径: `/api/merge-videos`
   - 请求方式: `POST`

3. 配置输入参数:
   - 参数名称: `video_urls`, 描述: "视频URL列表", 类型: `ARRAY`, 传入方法: `JSON`
   - 参数名称: `transition_type`, 描述: "转场类型", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `transition_duration`, 描述: "转场时长(秒)", 类型: `NUMBER`, 传入方法: `JSON`
   - 参数名称: `output_quality`, 描述: "输出质量", 类型: `STRING`, 传入方法: `JSON`
   - 参数名称: `output_resolution`, 描述: "输出分辨率(如:1280x720)", 类型: `STRING`, 传入方法: `JSON`

4. 配置输出参数:
   - 参数名称: `status`, 描述: "处理状态", 类型: `STRING`
   - 参数名称: `video_url`, 描述: "生成的视频URL", 类型: `STRING`
   - 参数名称: `error`, 描述: "错误信息", 类型: `STRING`

## 六、常见问题

### 服务无法启动
检查日志文件：
```bash
tail -f /home/你的用户名/image2video/api/logs/api.log
```

### Nginx配置有误
检查Nginx错误日志：
```bash
sudo tail -f /var/log/nginx/error.log
```

### 服务器防火墙问题
确保开放了80端口：
```bash
# CentOS/RHEL
sudo firewall-cmd --list-all
# Ubuntu
sudo ufw status
```

### 权限问题
确保目录有正确的权限：
```bash
chmod -R 755 /home/你的用户名/image2video/api
```

### 资源监控
定期检查服务器磁盘空间和资源使用情况：
```bash
df -h  # 检查磁盘空间
free -m  # 检查内存使用
top  # 检查CPU使用
``` 