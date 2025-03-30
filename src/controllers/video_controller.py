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
    
    def generate_clip(self, item: ImageItem) -> str:
        """
        生成单个视频片段
        
        Args:
            item: 图片项目
            
        Returns:
            生成的视频片段路径
        """
        try:
            # 检查并生成音频（如果有文本但没有音频）
            if item.text.strip() and not item.has_audio:
                self.audio_controller.generate_audio_for_item(item)
            
            # 获取图片名称（不含扩展名）
            image_filename = os.path.splitext(os.path.basename(str(item.image_path)))[0]
            
            # 生成以图片名称为基础的输出文件名
            output_filename = f"{image_filename}_clip.mp4"
            
            # 生成视频片段
            output_path = self.video_service.preview_clip(item.to_dict(), output_filename)
            
            return output_path
            
        except Exception as e:
            print(f"生成视频片段失败: {str(e)}")
            raise
    
    def generate_video(self, items: List[ImageItem], settings: Dict) -> str:
        """
        生成完整视频
        
        Args:
            items: 图片项目列表
            settings: 视频生成设置
            
        Returns:
            生成的视频文件路径
        """
        if not items:
            raise ValueError("没有提供要处理的项目")
            
        try:
            # 检查并生成缺失的音频
            self._ensure_audio_for_items(items)
            
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