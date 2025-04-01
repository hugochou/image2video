#!/usr/bin/env python3
"""
图片转视频API测试脚本
用于测试API服务是否正常工作
"""

import requests
import json
import base64
import os
import time
import argparse
from pathlib import Path

# 默认API地址
DEFAULT_API_URL = "http://localhost:5000"

def test_health_check(api_url):
    """测试健康检查接口"""
    print("测试健康检查接口...")
    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            print("健康检查成功: ", response.json())
            return True
        else:
            print(f"健康检查失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"健康检查请求异常: {str(e)}")
        return False

def test_image_to_video(api_url, image_path, animation_type="放大", animation_curve="线性", duration=5.0):
    """测试图片转视频接口"""
    print(f"测试图片转视频接口，使用图片: {image_path}...")
    
    # 读取图片并编码为base64
    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 构建请求数据
    data = {
        "image_base64": image_base64,
        "animation_type": animation_type,
        "animation_curve": animation_curve,
        "duration": duration
    }
    
    # 发送请求
    try:
        print("发送请求中...")
        response = requests.post(f"{api_url}/api/image2video", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("图片转视频成功!")
            print("视频URL: ", result["video_url"])
            return result["video_url"]
        else:
            print(f"图片转视频失败，状态码: {response.status_code}")
            print("错误信息: ", response.text)
            return None
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None

def download_video(video_url, output_path):
    """下载视频文件"""
    print(f"下载视频到: {output_path}...")
    try:
        response = requests.get(video_url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"视频下载成功: {output_path}")
            file_size = os.path.getsize(output_path) / 1024
            print(f"文件大小: {file_size:.2f} KB")
            return True
        else:
            print(f"视频下载失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"下载异常: {str(e)}")
        return False

def test_merge_videos(api_url, video_paths, transition_type="淡入淡出", transition_duration=0.7):
    """测试视频合成接口"""
    print(f"测试视频合成接口，使用 {len(video_paths)} 个视频...")
    
    # 由于我们没有公开的视频URL，这里我们先使用本地图片生成视频
    video_urls = []
    for i, image_path in enumerate(video_paths):
        print(f"为图片 {i+1}/{len(video_paths)} 生成视频: {image_path}")
        video_url = test_image_to_video(api_url, image_path, 
                                        animation_type=["放大", "缩小", "左到右", "右到左"][i % 4],
                                        duration=3.0)
        if video_url:
            video_urls.append(video_url)
    
    if len(video_urls) < 2:
        print("生成的视频不足两个，无法测试合成功能")
        return None
    
    # 构建请求数据
    data = {
        "video_urls": video_urls,
        "transition_type": transition_type,
        "transition_duration": transition_duration,
        "output_quality": "medium"
    }
    
    # 发送请求
    try:
        print("发送视频合成请求...")
        response = requests.post(f"{api_url}/api/merge-videos", json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("视频合成成功!")
            print("合成视频URL: ", result["video_url"])
            return result["video_url"]
        else:
            print(f"视频合成失败，状态码: {response.status_code}")
            print("错误信息: ", response.text)
            return None
    except Exception as e:
        print(f"请求异常: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="图片转视频API测试工具")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API服务地址")
    parser.add_argument("--image", help="测试用图片路径")
    parser.add_argument("--images-dir", help="包含多张图片的目录，用于测试视频合成")
    parser.add_argument("--output", default="./test_output", help="输出目录")
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # 测试健康检查
    if not test_health_check(args.api_url):
        print("健康检查失败，请确保API服务正在运行")
        return
    
    # 测试图片转视频
    if args.image:
        video_url = test_image_to_video(args.api_url, args.image)
        if video_url:
            download_video(video_url, output_dir / "output_video.mp4")
    
    # 测试视频合成
    if args.images_dir:
        images_dir = Path(args.images_dir)
        image_paths = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        if len(image_paths) >= 2:
            merged_url = test_merge_videos(args.api_url, image_paths[:4])
            if merged_url:
                download_video(merged_url, output_dir / "merged_video.mp4")
        else:
            print(f"目录 {args.images_dir} 中没有足够的图片用于测试视频合成")

if __name__ == "__main__":
    main() 