from moviepy.editor import (ImageClip, AudioFileClip, concatenate_videoclips, 
                          VideoFileClip, CompositeVideoClip, vfx, transfx, VideoClip)
from pathlib import Path
from typing import List, Dict, Union, Optional, Tuple
import os
import subprocess
import platform
import random
from PIL import Image
import numpy as np
import time
import cv2
import uuid
import traceback
import datetime
import os.path

# 修复 Pillow 兼容性问题
try:
    Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    Image.ANTIALIAS = Image.LANCZOS

from ..models.image_item import ImageItem
from .animation_service import AnimationService
from .transition_service import TransitionService
from .path_service import PathService

class VideoService:
    """视频服务，处理视频的生成和编辑"""
    
    def __init__(self):
        self.path_service = PathService()
        self.default_duration = 5  # 默认每个片段的持续时间
        self.default_fps = 30      # 默认帧率
        
        # 初始化动画服务
        self.animation_service = AnimationService()
        
        # 初始化转场服务
        self.transition_service = TransitionService()
        
        # 提供对所有转场的访问
        self.transitions = self.transition_service.transitions
    
    def create_clip(self, item: Dict) -> VideoClip:
        """
        为单个图片创建视频片段，支持各种效果
        
        Args:
            item: 包含图片路径、持续时间、音频路径、动画效果等
            
        Returns:
            创建的视频片段
        """
        # 创建图像片段
        image_path = item.get("image_path")
        # 确保路径是字符串
        if hasattr(image_path, '__fspath__'):  # 检查是否是Path对象
            image_path = str(image_path)
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件未找到: {image_path}")
        
        # 获取片段ID（如果有）
        clip_id = item.get("id", None)
        # 获取图片文件名（不含扩展名）
        image_filename = os.path.splitext(os.path.basename(image_path))[0]
        print(f"\n===== 开始创建片段 {clip_id} (图片: {image_filename}) =====")
        
        # 先获取音频时长（如果有音频）
        audio_path = item.get("audio_path")
        audio_clip = None
        audio_duration = 0
        
        if audio_path:
            # 确保路径是字符串
            if hasattr(audio_path, '__fspath__'):
                audio_path = str(audio_path)
            
            if os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
                print(f"检测到音频: {audio_path}, 时长: {audio_duration:.2f}秒")
        
        # 确定视频片段时长：优先使用音频时长，其次是用户指定时长，最后是默认时长
        if audio_duration > 0:
            duration = audio_duration
            print(f"使用音频时长 {duration:.2f}秒 作为视频片段时长")
        else:
            duration = item.get("duration", self.default_duration)
            print(f"使用指定时长 {duration:.2f}秒 作为视频片段时长")
        
        # 加载图像
        image_clip = ImageClip(image_path).set_duration(duration)
        
        # 应用动画效果
        animation = item.get("animation")
        if animation:
            # 获取动画设置
            animation_settings = self.animation_service.get_animation_settings(animation)
            # 打印动画设置
            print(f"应用动画效果: {animation_settings}")
            # 获取并打印曲线参数（用于调试）
            curve_name = animation_settings.get('curve', '线性')
            curve_func = self.animation_service.get_curve_function(curve_name)
            print(f"曲线'{curve_name}'在不同时间点的值:")
            for i in range(11):
                t = i / 10
                print(f"  t={t:.1f}, value={curve_func(t):.4f}")
            # 应用动画效果
            image_clip = self.apply_opencv_animation(image_clip, animation_settings, duration, clip_id)
        
        # 设置音频（如果有）
        if audio_clip:
            # 设置音频
            image_clip = image_clip.set_audio(audio_clip)
            print(f"已添加音频: {audio_path}, 持续时间: {audio_clip.duration:.2f}s")
        
        print(f"===== 片段 {clip_id} (图片: {image_filename}) 创建完成，持续时间: {duration:.2f}s =====\n")
        
        return image_clip
    
    def apply_opencv_animation(self, clip, animation_params, duration, clip_id=None):
        """
        使用OpenCV实现高精度的动画效果（包括缩放和位移）
        
        Args:
            clip: 原始视频片段
            animation_params: 动画参数，包括scale和position
            duration: 动画持续时间
            clip_id: 片段ID，用于日志标识
            
        Returns:
            应用了动画效果的视频片段
        """
        # 从动画参数中获取缩放和位移信息
        start_scale, end_scale = animation_params.get('scale', [1.0, 1.0])
        start_pos, end_pos = animation_params.get('position', [(0, 0), (0, 0)])
        curve_name = animation_params.get('curve', '线性')
        
        # 获取曲线函数
        curve_func = self.animation_service.get_curve_function(curve_name)
        
        # 为日志添加片段ID标识
        clip_identifier = f"[片段{clip_id}]" if clip_id else ""
        
        # 打印更详细的动画参数
        print(f"\n{clip_identifier}开始处理视频片段，应用动画:")
        print(f"{clip_identifier}动画时长: {duration:.2f}秒")
        print(f"{clip_identifier}缩放: 起始={start_scale:.2f} -> 结束={end_scale:.2f}")
        print(f"{clip_identifier}位移: 起始=({start_pos[0]:.3f}, {start_pos[1]:.3f}) -> 结束=({end_pos[0]:.3f}, {end_pos[1]:.3f})")
        print(f"{clip_identifier}曲线: '{curve_name}'")
        
        # 打印曲线值，用于调试
        print(f"{clip_identifier}曲线'{curve_name}'在不同时间点的值:")
        for i in range(11):
            t = i / 10
            print(f"{clip_identifier}  t={t:.1f}, value={curve_func(t):.4f}")
        
        # 预计算每一帧的参数 - 使用更多的采样点进行过采样，减少抖动
        # 通过预计算和高精度插值减少抖动
        frame_count = int(duration * self.default_fps * 3)  # 3倍过采样
        print(f"{clip_identifier}t=0.00, progress=0.0000, curve_value=0.0000, scale={start_scale:.4f}")
        
        # 定义处理函数
        def process_frame(get_frame, t):
            # 获取原始帧
            frame = get_frame(t)
            
            # 计算动画进度
            progress = min(1.0, t / duration) if duration > 0 else 1.0
            
            # 使用曲线函数获取动画曲线值
            curve_value = curve_func(progress)
            
            # 计算当前缩放值
            current_scale = start_scale + (end_scale - start_scale) * curve_value
            
            # 计算当前位移
            start_x, start_y = start_pos
            end_x, end_y = end_pos
            current_x = start_x + (end_x - start_x) * curve_value
            current_y = start_y + (end_y - start_y) * curve_value
            
            # 如果是第一次处理该时间点，打印调试信息
            if int(t * 100) % 3 == 0:  # 每0.03秒打印一次
                print(f"{clip_identifier}t={t:.2f}, progress={progress:.4f}, curve_value={curve_value:.4f}, scale={current_scale:.4f}, pos=({current_x:.4f}, {current_y:.4f})")
            
            # 使用OpenCV进行高质量缩放和移动
            h, w = frame.shape[:2]
            
            # 计算平移后是否会有黑边
            max_x_shift = abs(current_x)
            max_y_shift = abs(current_y)
            
            # 如果有平移，增加缩放以防止黑边
            if max_x_shift > 0 or max_y_shift > 0:
                # 计算需要增加的缩放比例，确保移动后不会露出黑边
                border_scale = max(1.0, 1.0 + 2 * max_x_shift, 1.0 + 2 * max_y_shift)
                # 合并当前缩放和防黑边缩放
                effective_scale = current_scale * border_scale
                
                # 调整缩放矩阵
                M_scale = np.float32([
                    [effective_scale, 0, w * (1 - effective_scale) / 2],
                    [0, effective_scale, h * (1 - effective_scale) / 2]
                ])
            else:
                # 没有平移，使用原始缩放
                M_scale = np.float32([
                    [current_scale, 0, w * (1 - current_scale) / 2],
                    [0, current_scale, h * (1 - current_scale) / 2]
                ])
            
            # 计算位移矩阵
            M_translate = np.float32([
                [1, 0, current_x * w],
                [0, 1, current_y * h]
            ])
            
            # 应用缩放
            if current_scale != 1.0:
                frame = cv2.warpAffine(frame, M_scale, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            
            # 应用位移
            if current_x != 0 or current_y != 0:
                frame = cv2.warpAffine(frame, M_translate, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            
            return frame
        
        # 将处理函数应用到片段
        return clip.fl(lambda gf, t: process_frame(gf, t))
    
    def create_video(self, items: List[dict], output_path: str, 
                    transition: str = "淡入淡出", transition_duration: float = 0.7,
                    advanced_options: Optional[Dict] = None) -> str:
        """
        创建完整视频，支持多种转场效果和高级设置
        
        Args:
            items: 包含图片、音频和动画设置的项目列表
            output_path: 输出视频文件路径
            transition: 转场效果名称
            transition_duration: 转场效果持续时间（秒）
            advanced_options: 高级设置选项，包括：
                - use_custom_transitions: 是否使用自定义转场（为每个片段指定不同的转场）
                - custom_transitions: 自定义转场列表，与项目数量-1对应
                - video_resolution: 视频分辨率 (width, height)
                - output_quality: 输出质量 (low, medium, high)
        
        Returns:
            生成的视频文件路径
        """
        if not items:
            raise ValueError("没有提供要处理的项目")
        
        # 处理高级选项
        advanced_options = advanced_options or {}
        use_custom_transitions = advanced_options.get('use_custom_transitions', False)
        custom_transitions = advanced_options.get('custom_transitions', [])
        video_resolution = advanced_options.get('video_resolution', None)
        output_quality = advanced_options.get('output_quality', 'medium')
        
        # 生成基于日期时间的视频文件名
        now = datetime.datetime.now()
        date_time_str = now.strftime("%Y%m%d_%H%M")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成新的输出路径，使用时间戳
        # 基于原始输出路径获取目录
        original_dir = os.path.dirname(output_path)
        
        # 生成新的文件名（使用时间戳+随机数）
        random_id = str(uuid.uuid4())[:4]
        new_filename = f"final_{date_time_str}_{random_id}.mp4"
        
        # 组合新的输出路径
        output_path = os.path.join(original_dir, new_filename)
        
        clips = []
        original_clips = []
        
        try:
            print("\n" + "="*50)
            print(f"开始创建视频 - 共 {len(items)} 个片段")
            print(f"转场效果: {transition}, 时长: {transition_duration}秒")
            print(f"输出文件: {output_path}")
            if video_resolution:
                print(f"输出分辨率: {video_resolution[0]}x{video_resolution[1]}")
            print(f"输出质量: {output_quality}")
            if use_custom_transitions:
                print(f"使用自定义转场: {custom_transitions}")
            print("="*50 + "\n")
            
            # 创建每个片段
            print(f"正在处理 {len(items)} 个视频片段...")
            for i, item in enumerate(items):
                print(f"\n{'*'*30}")
                print(f"创建片段 {i+1}/{len(items)}...")
                
                # 检查是否需要先生成音频（如果有文本但没有音频）
                if 'text' in item and item['text'] and ('audio_path' not in item or not item['audio_path']):
                    # 需要先生成音频，这部分会在controller层实现
                    print(f"片段 {i+1} 有文本但无音频，将由控制器处理")
                
                clip = self.create_clip(item)
                
                # 如果指定了视频分辨率，调整所有片段的尺寸
                if video_resolution:
                    clip = clip.resize(video_resolution)
                    print(f"已调整片段 {i+1} 的分辨率为 {video_resolution[0]}x{video_resolution[1]}")
                
                original_clips.append(clip)
                clips.append(clip)
                
                # 获取图片文件名
                image_path = item.get("image_path", "")
                if isinstance(image_path, Path):
                    image_path = str(image_path)
                image_filename = os.path.splitext(os.path.basename(image_path))[0] if image_path else f"segment_{i+1}"
                
                print(f"片段 {i+1} ({image_filename}) 创建完成，持续时间: {clip.duration:.2f}秒")
                print(f"{'*'*30}\n")
            
            # 应用过渡效果
            if len(clips) > 1 and (transition or use_custom_transitions):
                print("\n" + "-"*40)
                print("开始应用转场效果...")
                # 使用新的转场服务
                if use_custom_transitions and custom_transitions:
                    # 创建一个合成视频，其中包含定制的转场效果
                    print(f"应用自定义转场效果: {custom_transitions}")
                    final_clip = self.transition_service.create_composite_transition(
                        clips, 
                        transition, 
                        transition_duration,
                        custom_transitions
                    )
                else:
                    # 应用常规的转场效果
                    print(f"应用转场效果: {transition}，时长: {transition_duration}秒")
                    clips = self.transition_service.apply_transitions_to_clips(
                        clips, 
                        transition, 
                        transition_duration,
                        use_custom_transitions,
                        custom_transitions
                    )
                    
                    # 将所有片段连接起来
                    print("合并所有视频片段...")
                    final_clip = concatenate_videoclips(clips, method="compose")
                print(f"转场效果应用完成，最终视频时长: {final_clip.duration:.2f}秒")
                print("-"*40 + "\n")
            else:
                # 无转场效果，直接连接
                print("合并所有视频片段（无转场）...")
                final_clip = concatenate_videoclips(clips, method="compose")
            
            # 检查最后一个片段是否有音频，如果有，确保视频长度不会导致音频被截断
            if len(original_clips) > 0 and original_clips[-1].audio is not None:
                last_clip = original_clips[-1]
                last_audio = last_clip.audio
                
                # 计算原始片段的总时长（不含转场）
                original_duration = sum(clip.duration for clip in original_clips)
                
                # 计算最后片段的结束时间
                last_clip_end_time = original_duration
                
                # 计算最后一个音频的结束时间
                last_audio_end_time = last_clip_end_time
                
                # 如果最后一个音频的结束时间超过了视频的总时长，需要延长视频
                if last_audio_end_time > final_clip.duration:
                    # 创建一个静态片段来延长视频
                    print(f"延长视频以确保音频播放完整 (音频结束时间: {last_audio_end_time:.2f}s, 当前视频时长: {final_clip.duration:.2f}s)")
                    padding_duration = last_audio_end_time - final_clip.duration
                    
                    # 获取最后一帧作为延长片段的图像
                    last_frame = final_clip.get_frame(final_clip.duration - 0.1)
                    padding_clip = ImageClip(last_frame).set_duration(padding_duration)
                    
                    # 将延长片段添加到视频末尾
                    final_clip = concatenate_videoclips([final_clip, padding_clip], method="compose")
                    print(f"视频已延长，新时长: {final_clip.duration:.2f}秒")
            
            # 根据质量设置输出参数
            bitrate = None
            if output_quality == 'low':
                bitrate = '1000k'
            elif output_quality == 'medium':
                bitrate = '2500k'
            elif output_quality == 'high':
                bitrate = '5000k'
            
            print(f"\n正在导出视频到 {output_path}...")
            if bitrate:
                print(f"使用比特率: {bitrate}")
            
            # 写入视频文件
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                bitrate=bitrate,
                fps=self.default_fps,
                threads=4
            )
            
            print("清理临时资源...")
            # 释放资源
            final_clip.close()
            for clip in clips:
                if hasattr(clip, 'close'):
                    clip.close()
            
            print(f"视频生成完成: {output_path}")
            print("="*50 + "\n")
            
            return output_path
            
        except Exception as e:
            # 清理资源
            for clip in clips:
                if hasattr(clip, 'close'):
                    try:
                        clip.close()
                    except:
                        pass
            
            print(f"生成视频时出错: {str(e)}")
            traceback.print_exc()
            raise
    
    def preview_clip(self, item: dict, output_filename: str) -> str:
        """预览单个片段"""
        try:
            # 确保item中的路径是字符串
            preview_item = item.copy()
            
            if "image_path" in preview_item and hasattr(preview_item["image_path"], '__fspath__'):
                preview_item["image_path"] = str(preview_item["image_path"])
                
            if "audio_path" in preview_item and preview_item["audio_path"] and hasattr(preview_item["audio_path"], '__fspath__'):
                preview_item["audio_path"] = str(preview_item["audio_path"])
            
            # 使用图片文件名作为输出文件名的一部分
            image_path = preview_item.get("image_path", "")
            image_filename = os.path.splitext(os.path.basename(image_path))[0] if image_path else "clip"
            
            # 创建基于图片名称的输出文件名
            if not output_filename:
                output_filename = f"preview_{image_filename}_{uuid.uuid4()}.mp4"
            
            # 创建片段
            clip = self.create_clip(preview_item)
            
            # 获取视频目录
            video_dir = self.path_service.video_directory
            video_dir.mkdir(parents=True, exist_ok=True)
            output_path = video_dir / output_filename
            
            # 写入预览文件
            clip.write_videofile(
                str(output_path), 
                codec='libx264',
                fps=self.default_fps,
                threads=min(4, os.cpu_count() or 2),
                preset='medium',
                audio_codec='aac' if clip.audio is not None else None
            )
            
            # 关闭剪辑
            clip.close()
            
            # 返回预览文件路径
            return str(output_path)
        except Exception as e:
            raise Exception(f"生成预览失败: {str(e)}")
    
    def open_with_default_player(self, file_path: str):
        """使用系统默认播放器打开视频"""
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", file_path])
            else:  # Linux
                subprocess.call(["xdg-open", file_path])
            return True
        except Exception as e:
            print(f"打开文件失败: {str(e)}")
            return False 