#!/bin/bash

# 确保在脚本所在目录运行
cd "$(dirname "$0")"

# 删除超过3天的文件
echo "开始清理超过3天的临时文件..."

# 清理上传目录
find api_uploads -type f -mtime +3 -delete
echo "已清理上传目录中的旧文件"

# 清理输出目录
find api_output -type f -mtime +3 -delete
echo "已清理输出目录中的旧文件"

# 清理临时目录
find api_temp -type f -mtime +3 -delete
echo "已清理临时目录中的旧文件"

# 清理日志文件（保留最近7天）
find logs -type f -name "*.log" -mtime +7 -delete
echo "已清理超过7天的日志文件"

echo "清理完成！" 