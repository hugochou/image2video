from typing import List, Dict, Optional
from pathlib import Path
import os

from ..services.audio_service import AudioService
from ..models.image_item import ImageItem

class AudioController:
    """音频控制器，处理音频生成相关的业务逻辑"""
    
    def __init__(self, audio_service: AudioService):
        """
        初始化音频控制器
        
        Args:
            audio_service: 音频服务实例
        """
        self.audio_service = audio_service
    
    def generate_audio_for_item(self, item: ImageItem) -> bool:
        """
        为单个图片项目生成音频
        
        Args:
            item: 图片项目
            
        Returns:
            是否成功生成音频
        """
        if not item.text.strip():
            return False
        
        try:
            # 获取图片文件名（不含扩展名）
            image_path = str(item.image_path) if isinstance(item.image_path, Path) else item.image_path
            image_name = os.path.basename(image_path)
            
            # 生成音频文件
            audio_path = self.audio_service.generate_speech(
                item.text,
                f"{item.id}.mp3",  # 默认文件名使用ID
                image_name         # 优先使用图片名称
            )
            
            if audio_path:
                item.audio_path = audio_path
                return True
                
            return False
            
        except Exception as e:
            print(f"生成音频失败: {str(e)}")
            return False
    
    def batch_generate_audio(self, items: List[ImageItem]) -> Dict[str, bool]:
        """
        批量生成音频
        
        Args:
            items: 图片项目列表
            
        Returns:
            字典，键为项目ID，值为是否成功生成音频
        """
        results = {}
        
        for item in items:
            success = self.generate_audio_for_item(item)
            results[item.id] = success
            
        return results
    
    def check_and_generate_missing_audio(self, items: List[ImageItem]) -> Dict[str, bool]:
        """
        检查并生成缺失的音频
        
        Args:
            items: 图片项目列表
            
        Returns:
            字典，键为项目ID，值为是否成功生成音频
        """
        results = {}
        
        for item in items:
            # 检查是否有文本但没有音频或音频不存在
            if item.text.strip() and (not item.audio_path or not item.audio_path.exists()):
                success = self.generate_audio_for_item(item)
                results[item.id] = success
        
        return results
    
    def preview_audio(self, item: ImageItem) -> bool:
        """
        预览音频
        
        Args:
            item: 图片项目
            
        Returns:
            是否成功播放
        """
        if not item.has_audio:
            return False
            
        try:
            self.audio_service.preview_audio(str(item.audio_path))
            return True
        except Exception as e:
            print(f"预览音频失败: {str(e)}")
            return False 