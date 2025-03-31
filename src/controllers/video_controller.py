from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import os

from ..services.video_service import VideoService
from ..services.audio_service import AudioService
from ..controllers.audio_controller import AudioController
from ..models.image_item import ImageItem

class VideoController:
    """视频控制器，处理视频生成相关的业务逻辑"""
    
    def __init__(self, video_service: VideoService, audio_service: AudioService):
        """
        初始化视频控制器
        
        Args:
            video_service: 视频服务实例
            audio_service: 音频服务实例
        """
        self.video_service = video_service
        self.audio_service = audio_service
        self.audio_controller = AudioController(audio_service)
        
        # 存储最近生成的视频路径
        self.last_video_path = None
        # 存储已生成的片段，格式：{图片路径: 视频片段路径}
        self.generated_clips = {}
    
    def _get_clip_filename(self, item: ImageItem) -> str:
        """
        根据图片生成统一的片段文件名
        
        Args:
            item: 图片项目
            
        Returns:
            生成的文件名
        """
        image_filename = os.path.splitext(os.path.basename(str(item.image_path)))[0]
        return f"{image_filename}_clip.mp4"
    
    def _get_clip_filepath(self, item: ImageItem) -> str:
        """
        获取片段的完整文件路径
        
        Args:
            item: 图片项目
            
        Returns:
            片段文件的完整路径
        """
        filename = self._get_clip_filename(item)
        return str(self.video_service.path_service.video_directory / filename)
    
    def is_clip_generated(self, item: ImageItem) -> bool:
        """
        检查片段是否已经生成
        
        Args:
            item: 图片项目
            
        Returns:
            如果片段已生成则返回True，否则返回False
        """
        # 获取图片路径的字符串表示
        image_path_str = str(item.image_path)
        
        # 检查缓存中是否有该片段
        if image_path_str in self.generated_clips:
            clip_path = self.generated_clips[image_path_str]
            if os.path.exists(clip_path):
                return True
        
        # 检查文件系统中是否存在该片段
        clip_path = self._get_clip_filepath(item)
        if os.path.exists(clip_path):
            # 存在则更新缓存并返回True
            self.generated_clips[image_path_str] = clip_path
            return True
            
        return False
    
    def generate_clip(self, item: ImageItem) -> str:
        """
        生成单个视频片段，如已存在则直接返回
        
        Args:
            item: 图片项目
            
        Returns:
            生成的视频片段路径
        """
        try:
            # 获取图片路径的字符串表示
            image_path_str = str(item.image_path)
            
            # 检查是否已生成该片段
            if self.is_clip_generated(item):
                print(f"片段已存在，直接使用: {self.generated_clips[image_path_str]}")
                return self.generated_clips[image_path_str]
            
            # 检查并生成音频（如果有文本但没有音频）
            if item.text.strip() and not item.has_audio:
                self.audio_controller.generate_audio_for_item(item)
            
            # 生成以图片名称为基础的输出文件名
            output_filename = self._get_clip_filename(item)
            
            # 生成视频片段
            output_path = self.video_service.preview_clip(item.to_dict(), output_filename)
            
            # 缓存生成的片段路径
            self.generated_clips[image_path_str] = output_path
            
            return output_path
            
        except Exception as e:
            print(f"生成视频片段失败: {str(e)}")
            raise
    
    def preview_clip(self, item: ImageItem) -> bool:
        """
        预览单个片段，如已存在则直接预览，否则先生成再预览
        
        Args:
            item: 图片项目
            
        Returns:
            是否成功播放
        """
        try:
            # 检查是否已生成该片段
            if not self.is_clip_generated(item):
                # 没有生成则先生成片段
                clip_path = self.generate_clip(item)
            else:
                # 已生成则直接获取路径
                clip_path = self.generated_clips[str(item.image_path)]
                
            # 使用默认播放器预览
            return self.video_service.open_with_default_player(clip_path)
            
        except Exception as e:
            print(f"预览片段失败: {str(e)}")
            return False
    
    def generate_video(self, items: List[ImageItem], settings: Dict) -> str:
        """
        生成完整视频，会自动检查并生成缺失的片段
        
        Args:
            items: 图片项目列表
            settings: 视频生成设置
            
        Returns:
            生成的视频文件路径
        """
        if not items:
            raise ValueError("没有提供要处理的项目")
            
        try:
            print("准备生成完整视频...")
            
            # 检查并生成缺失的音频
            self._ensure_audio_for_items(items)
            
            # 检查并生成缺失的片段
            self._ensure_clips_for_items(items)
            
            # 创建输出目录
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # 生成视频
            output_path = self.video_service.create_video(
                [item.to_dict() for item in items],
                str(output_dir / "final_video.mp4"),
                settings["transition"],
                settings["transition_duration"],
                {
                    "use_custom_transitions": settings.get("use_custom_transitions", False),
                    "custom_transitions": settings.get("custom_transitions", []),
                    "video_resolution": settings.get("video_resolution", None),
                    "output_quality": settings.get("output_quality", "medium")
                }
            )
            
            # 存储最近生成的视频路径
            self.last_video_path = output_path
            
            return output_path
            
        except Exception as e:
            print(f"生成视频失败: {str(e)}")
            raise
    
    def preview_video(self, video_path: str = None) -> bool:
        """
        预览视频
        
        Args:
            video_path: 视频文件路径，如果未提供则使用最近生成的视频
            
        Returns:
            是否成功播放
        """
        try:
            if video_path:
                return self.video_service.open_with_default_player(video_path)
            elif self.last_video_path:
                return self.video_service.open_with_default_player(self.last_video_path)
            else:
                print("没有可预览的视频")
                return False
                
        except Exception as e:
            print(f"预览视频失败: {str(e)}")
            return False
    
    def _ensure_audio_for_items(self, items: List[ImageItem]) -> None:
        """
        确保所有带文本的项目都有对应的音频
        
        Args:
            items: 图片项目列表
        """
        # 使用音频控制器检查并生成缺失的音频
        self.audio_controller.check_and_generate_missing_audio(items)
    
    def _ensure_clips_for_items(self, items: List[ImageItem]) -> None:
        """
        确保所有项目都有对应的视频片段，如不存在则自动生成
        
        Args:
            items: 图片项目列表
        """
        for i, item in enumerate(items):
            if not self.is_clip_generated(item):
                print(f"正在生成缺失的片段 {i+1}/{len(items)}...")
                self.generate_clip(item)
            else:
                print(f"片段 {i+1}/{len(items)} 已存在，跳过生成")
        
    def create_animation_for_item(self, item: ImageItem, scale_preset: str, position_preset: str, curve: str) -> None:
        """
        为项目创建动画设置
        
        Args:
            item: 图片项目
            scale_preset: 缩放预设名称
            position_preset: 位移预设名称
            curve: 曲线名称
        """
        # 组合设置
        animation_settings = self.video_service.animation_service.combine_animation_settings(
            scale_preset, position_preset, curve
        )
        
        # 应用到item
        item.animation = animation_settings
        
        # 动画设置更改后，将相应的已生成片段标记为无效
        if str(item.image_path) in self.generated_clips:
            del self.generated_clips[str(item.image_path)] 