from flask import Flask, request, jsonify, send_file
import os
import sys
import tempfile
import shutil
import uuid
import requests
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import traceback
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 导入项目现有模块
from src.services.video_service import VideoService
from src.services.path_service import PathService
from src.services.animation_service import AnimationService
from src.services.transition_service import TransitionService

app = Flask(__name__)

# 配置日志
log_dir = os.path.join(current_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'api.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('image2video_api')

# 初始化服务
try:
    video_service = VideoService()
    animation_service = AnimationService()
    logger.info("服务初始化成功")
except Exception as e:
    logger.error(f"服务初始化失败: {str(e)}")
    traceback.print_exc()

# 配置上传和输出目录
UPLOAD_FOLDER = Path(os.path.join(current_dir, 'api_uploads'))
OUTPUT_FOLDER = Path(os.path.join(current_dir, 'api_output'))
TEMP_FOLDER = Path(os.path.join(current_dir, 'api_temp'))

# 创建必要的目录
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
TEMP_FOLDER.mkdir(exist_ok=True)

logger.info(f"上传目录: {UPLOAD_FOLDER}")
logger.info(f"输出目录: {OUTPUT_FOLDER}")
logger.info(f"临时目录: {TEMP_FOLDER}")

def download_file(url: str) -> Optional[str]:
    """
    下载文件到本地临时目录
    
    Args:
        url: 文件URL
        
    Returns:
        下载后的本地文件路径，如果下载失败则返回None
    """
    try:
        logger.info(f"开始下载文件: {url}")
        # 生成唯一文件名
        filename = str(uuid.uuid4())
        file_extension = os.path.splitext(url)[1]
        if not file_extension:
            # 如果URL没有文件扩展名，尝试从内容类型判断
            response = requests.head(url)
            content_type = response.headers.get('Content-Type', '')
            
            if 'image' in content_type:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    file_extension = '.jpg'
                elif 'png' in content_type:
                    file_extension = '.png'
                else:
                    file_extension = '.jpg'  # 默认jpg
            elif 'audio' in content_type:
                if 'mp3' in content_type:
                    file_extension = '.mp3'
                elif 'wav' in content_type:
                    file_extension = '.wav'
                else:
                    file_extension = '.mp3'  # 默认mp3
            else:
                file_extension = '.bin'  # 默认二进制
        
        local_path = UPLOAD_FOLDER / f"{filename}{file_extension}"
        
        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"文件下载成功: {local_path}")
        return str(local_path)
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return None

def decode_base64_image(base64_string: str) -> Optional[str]:
    """
    解码Base64字符串为图片文件
    
    Args:
        base64_string: Base64编码的图片数据
        
    Returns:
        保存后的图片文件路径，如果解码失败则返回None
    """
    try:
        logger.info("开始解码Base64图片")
        # 移除可能的前缀
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        # 解码Base64数据
        image_data = base64.b64decode(base64_string)
        
        # 生成唯一文件名
        filename = str(uuid.uuid4()) + '.jpg'  # 默认使用jpg格式
        local_path = UPLOAD_FOLDER / filename
        
        # 保存文件
        with open(local_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"Base64图片解码成功: {local_path}")
        return str(local_path)
    except Exception as e:
        logger.error(f"解码Base64图片失败: {str(e)}")
        return None

@app.route('/api/image2video', methods=['POST'])
def image_to_video():
    """
    将图片转换为视频的API端点
    
    接收参数:
    - image_url 或 image_base64: 图片URL或Base64编码
    - audio_url: 音频URL(可选)
    - animation_type: 动画类型(默认为"放大")
    - animation_curve: 动画曲线(默认为"线性")
    - duration: 视频时长(默认为5秒)
    - output_quality: 输出质量(默认为"medium")
    
    返回:
    - video_url: 生成的视频URL
    - status: 处理状态
    - error: 错误信息(如果有)
    """
    try:
        logger.info("收到图片转视频请求")
        # 获取请求参数
        json_data = request.get_json()
        
        # 检查是否有图片数据
        image_path = None
        if 'image_url' in json_data:
            image_path = download_file(json_data['image_url'])
        elif 'image_base64' in json_data:
            image_path = decode_base64_image(json_data['image_base64'])
        else:
            logger.error("缺少图片参数")
            return jsonify({
                'status': 'error',
                'error': '缺少图片参数(image_url或image_base64)'
            }), 400
        
        if not image_path:
            logger.error("图片处理失败")
            return jsonify({
                'status': 'error',
                'error': '图片处理失败'
            }), 400
        
        # 获取音频(如果有)
        audio_path = None
        if 'audio_url' in json_data and json_data['audio_url']:
            audio_path = download_file(json_data['audio_url'])
            if not audio_path:
                logger.error("音频下载失败")
                return jsonify({
                    'status': 'error',
                    'error': '音频下载失败'
                }), 400
        
        # 获取其他参数
        animation_type = json_data.get('animation_type', '放大')
        animation_curve = json_data.get('animation_curve', '线性')
        duration = float(json_data.get('duration', 5.0))
        output_quality = json_data.get('output_quality', 'medium')
        
        logger.info(f"处理参数: 动画={animation_type}, 曲线={animation_curve}, 时长={duration}秒")
        
        # 准备视频生成参数
        item = {
            'image_path': image_path,
            'audio_path': audio_path,
            'duration': duration,
            'animation': {
                'type': animation_type,
                'curve': animation_curve
            }
        }
        
        # 生成唯一的输出文件名
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = OUTPUT_FOLDER / output_filename
        
        logger.info(f"开始生成视频: {output_path}")
        
        # 调用视频服务生成视频
        video_path = video_service.preview_clip(item, str(output_path))
        
        # 构建视频URL
        server_url = request.host_url.rstrip('/')
        video_url = f"{server_url}/api/videos/{output_filename}"
        
        logger.info(f"视频生成成功: {video_url}")
        
        return jsonify({
            'status': 'success',
            'video_url': video_url
        })
        
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/merge-videos', methods=['POST'])
def merge_videos():
    """
    合并多个视频的API端点
    
    接收参数:
    - video_urls: 视频URL列表
    - transition_type: 转场类型(默认为"淡入淡出")
    - transition_duration: 转场时长(默认为0.7秒)
    - output_quality: 输出质量(默认为"medium")
    - output_resolution: 输出分辨率(可选)
    
    返回:
    - video_url: 生成的视频URL
    - status: 处理状态
    - error: 错误信息(如果有)
    """
    try:
        logger.info("收到视频合成请求")
        # 获取请求参数
        json_data = request.get_json()
        
        # 检查是否有视频URL列表
        if 'video_urls' not in json_data or not json_data['video_urls']:
            logger.error("缺少视频URL列表参数")
            return jsonify({
                'status': 'error',
                'error': '缺少视频URL列表参数'
            }), 400
        
        video_urls = json_data['video_urls']
        logger.info(f"合成视频数量: {len(video_urls)}")
        
        # 下载所有视频到本地
        video_paths = []
        for url in video_urls:
            path = download_file(url)
            if not path:
                logger.error(f"下载视频失败: {url}")
                return jsonify({
                    'status': 'error',
                    'error': f'下载视频失败: {url}'
                }), 400
            video_paths.append(path)
        
        # 获取其他参数
        transition_type = json_data.get('transition_type', '淡入淡出')
        transition_duration = float(json_data.get('transition_duration', 0.7))
        output_quality = json_data.get('output_quality', 'medium')
        output_resolution = json_data.get('output_resolution', None)
        
        logger.info(f"处理参数: 转场={transition_type}, 转场时长={transition_duration}秒")
        
        # 生成唯一的输出文件名
        output_filename = f"{uuid.uuid4()}.mp4"
        output_path = OUTPUT_FOLDER / output_filename
        
        # 导入MoviePy库来处理视频合并
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        # 加载所有视频片段
        video_clips = [VideoFileClip(path) for path in video_paths]
        
        # 如果指定了分辨率，调整所有片段的尺寸
        if output_resolution:
            width, height = map(int, output_resolution.split('x'))
            video_clips = [clip.resize((width, height)) for clip in video_clips]
            logger.info(f"设置输出分辨率: {width}x{height}")
        
        # 应用转场效果并合并视频
        if len(video_clips) > 1:
            # 调用视频服务的转场功能
            processed_clips = video_service.transition_service.apply_transitions_to_clips(
                video_clips, 
                transition_type, 
                transition_duration
            )
            
            # 合并处理后的片段
            final_clip = concatenate_videoclips(processed_clips, method="compose")
        else:
            # 只有一个片段，无需转场
            final_clip = video_clips[0]
        
        # 设置输出质量
        bitrate = '2500k'  # 默认中等质量
        if output_quality == 'low':
            bitrate = '1000k'
        elif output_quality == 'high':
            bitrate = '5000k'
        
        logger.info(f"开始写入视频文件: {output_path}, 质量={output_quality}")
        
        # 写入文件
        final_clip.write_videofile(
            str(output_path),
            codec='libx264',
            audio_codec='aac',
            bitrate=bitrate,
            fps=30,
            threads=4
        )
        
        # 构建视频URL
        server_url = request.host_url.rstrip('/')
        video_url = f"{server_url}/api/videos/{output_filename}"
        
        logger.info(f"视频合成成功: {video_url}")
        
        return jsonify({
            'status': 'success',
            'video_url': video_url
        })
        
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/videos/<filename>', methods=['GET'])
def get_video(filename):
    """
    提供生成的视频文件下载
    """
    try:
        video_path = OUTPUT_FOLDER / filename
        if not video_path.exists():
            logger.error(f"找不到请求的视频文件: {filename}")
            return jsonify({
                'status': 'error',
                'error': '找不到请求的视频文件'
            }), 404
        
        logger.info(f"提供视频下载: {filename}")
        return send_file(str(video_path), mimetype='video/mp4')
    except Exception as e:
        logger.error(f"提供视频下载时发生错误: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'ok',
        'message': 'Image2Video API服务正常运行'
    })

if __name__ == '__main__':
    logger.info("启动API服务器...")
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="Image2Video API服务器")
    parser.add_argument("--port", type=int, default=5000, help="服务器端口号")
    args = parser.parse_args()
    
    logger.info(f"使用端口 {args.port}")
    app.run(host="0.0.0.0", port=args.port, debug=False)