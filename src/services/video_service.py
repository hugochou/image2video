from moviepy.editor import (ImageClip, AudioFileClip, concatenate_videoclips, 
                          VideoFileClip, CompositeVideoClip, vfx, transfx, VideoClip)
from pathlib import Path
from typing import List
import os
import subprocess
import platform
import random
from PIL import Image
import numpy as np
import time

# 修复 Pillow 兼容性问题
try:
    Image.ANTIALIAS = Image.Resampling.LANCZOS
except AttributeError:
    Image.ANTIALIAS = Image.LANCZOS

from ..models.image_item import ImageItem
from .animation_service import AnimationService

class VideoService:
    def __init__(self):
        self.output_dir = Path("output")
        self.video_dir = self.output_dir / "video"
        self.preview_dir = self.video_dir / "previews"
        self.output_dir.mkdir(exist_ok=True)
        self.video_dir.mkdir(exist_ok=True)
        self.preview_dir.mkdir(exist_ok=True)
        self.default_duration = 5  # 默认每个片段的持续时间
        self.default_fps = 30      # 默认帧率
        
        # 初始化动画服务
        self.animation_service = AnimationService()
        
        # 定义所有可用的过渡效果
        self.transitions = {
            "淡入淡出": transfx.fadein,
            "滑动": transfx.slide_in,
            "缩放淡入": transfx.fadein,
            "旋转淡入": transfx.fadein,
            "交叉淡入淡出": transfx.crossfadein,
            "交叉淡出": transfx.crossfadeout,
            "随机": None  # 随机效果
        }
    
    def create_clip(self, item: dict) -> ImageClip:
        """创建单个视频片段"""
        # 如果有音频，先加载音频并获取实际时长
        audio_duration = None
        audio_clip = None
        if item.get('audio_path'):
            try:
                audio_clip = AudioFileClip(str(item['audio_path']))
                audio_duration = audio_clip.duration
            except Exception as e:
                if audio_clip:
                    audio_clip.close()
                raise Exception(f"加载音频文件失败: {str(e)}")
        
        # 设置基本参数
        duration = item.get('duration', self.default_duration)
        if audio_duration is not None:
            duration = audio_duration
        
        # 获取图像路径
        image_path = str(item['image_path'])
        
        # 获取动画设置
        animation_settings = item.get('animation')
        
        try:
            # 创建具有动画效果的视频片段
            print(f"应用动画效果: {animation_settings}")
            animated_clip = self.animation_service.apply_animation(
                image_path=image_path,
                animation_settings=animation_settings,
                duration=duration
            )
            
            # 添加音频
            if audio_clip:
                animated_clip = animated_clip.set_audio(audio_clip)
            
            # 设置最终时长
            animated_clip = animated_clip.set_duration(duration)
            
            return animated_clip
            
        except Exception as e:
            if audio_clip:
                audio_clip.close()
            raise Exception(f"创建视频片段失败: {str(e)}")
    
    def create_video(self, items: List[dict], output_path: str, 
                    transition: str = None, transition_duration: float = 0.5):
        """创建完整视频"""
        if not items:
            raise ValueError("没有提供要处理的项目")
        
        clips = []
        original_clips = []
        
        try:
            # 创建每个片段
            for item in items:
                clip = self.create_clip(item)
                original_clips.append(clip)
                clips.append(clip)
            
            # 应用过渡效果
            if transition:
                transition_fn = self.transitions.get(transition)
                if transition == "随机":
                    transition_options = list(self.transitions.keys())
                    transition_options.remove("随机")
                    random_transition = random.choice(transition_options)
                    transition_fn = self.transitions[random_transition]
                    print(f"选择随机过渡效果: {random_transition}")
                
                if transition_fn:
                    # 应用过渡效果
                    for i in range(len(clips)):
                        if i > 0:  # 不对第一个片段应用过渡效果
                            clips[i] = transition_fn(clips[i], transition_duration)
            
            # 将所有片段连接起来
            final_clip = concatenate_videoclips(clips)
            
            # 创建输出目录
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存视频
            final_clip.write_videofile(
                str(output_path),
                codec='libx264',
                fps=self.default_fps,
                threads=min(4, os.cpu_count() or 2),
                preset='medium',  # 设置压缩预设为 medium，平衡质量和时间
                audio_codec='aac' if any(c.audio is not None for c in clips) else None
            )
            
            # 清理临时剪辑
            for clip in original_clips:
                clip.close()
            final_clip.close()
            
            return str(output_path)
        
        except Exception as e:
            # 清理临时剪辑
            for clip in original_clips:
                try:
                    clip.close()
                except:
                    pass
            raise e
    
    def preview_clip(self, item: dict, output_filename: str) -> str:
        """预览单个片段"""
        try:
            # 创建片段
            clip = self.create_clip(item)
            
            # 确保输出目录存在
            self.preview_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.preview_dir / output_filename
            
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