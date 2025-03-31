import os
from pathlib import Path
from typing import Optional, List
from gtts import gTTS
import subprocess
import platform
import os.path
from .path_service import PathService

class AudioService:
    def __init__(self):
        self.path_service = PathService()
    
    def generate_speech(self, text: str, filename: str, image_name: str = None) -> Optional[Path]:
        """
        使用 Google Text-to-Speech 生成语音
        
        Args:
            text: 要转换的文本
            filename: 音频文件名（优先级低于image_name）
            image_name: 关联的图片名称（如果提供，将使用此名称作为音频文件名）
            
        Returns:
            成功返回音频文件路径，失败返回 None
        """
        try:
            # 获取音频目录
            audio_dir = self.path_service.audio_directory
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果提供了图片名称，使用它作为音频文件名
            if image_name:
                # 去除扩展名，如果有的话
                image_base_name = os.path.splitext(os.path.basename(image_name))[0]
                output_filename = f"{image_base_name}.mp3"
            else:
                output_filename = filename
            
            # 构建完整的输出路径
            output_path = audio_dir / output_filename
            
            # 使用 gTTS 生成语音
            tts = gTTS(text=text, lang='zh-cn')
            tts.save(str(output_path))
            
            print(f"已生成音频: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成语音时出错: {str(e)}")
            return None
    
    def preview_audio(self, audio_path: str):
        """
        预览音频文件
        
        Args:
            audio_path: 音频文件路径
        """
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['afplay', audio_path])
            elif platform.system() == 'Windows':
                os.startfile(audio_path)
            else:  # Linux
                subprocess.Popen(['xdg-open', audio_path])
        except Exception as e:
            print(f"预览音频时出错: {str(e)}")
            raise
    
    def batch_generate_speech(self, items: List[dict]) -> List[str]:
        """
        批量生成语音文件
        
        Args:
            items: 包含文本和文件名的字典列表，每个字典可以包含：
                - text: 转换为语音的文本
                - filename: 输出文件名
                - image_path: 图片路径（可选，如果提供将使用图片名称）
            
        Returns:
            生成的音频文件路径列表
        """
        results = []
        for item in items:
            if 'text' in item:
                # 从图片路径获取基本文件名，如果有
                image_name = None
                if 'image_path' in item and item['image_path']:
                    image_path = item['image_path']
                    if isinstance(image_path, Path):
                        image_path = str(image_path)
                    image_name = os.path.basename(image_path)
                
                # 确定文件名
                filename = item.get('filename', f"audio_{len(results)}.mp3")
                
                # 生成音频
                audio_path = self.generate_speech(item['text'], filename, image_name)
                if audio_path:
                    results.append(str(audio_path))
        return results 