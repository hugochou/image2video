import os
from pathlib import Path
from typing import Optional, List
from gtts import gTTS
import subprocess
import platform

class AudioService:
    def __init__(self):
        self.output_dir = Path("output")
        self.audio_dir = self.output_dir / "audio"
        self.output_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
    
    def generate_speech(self, text: str, filename: str) -> Optional[Path]:
        """
        使用 Google Text-to-Speech 生成语音
        
        Args:
            text: 要转换的文本
            filename: 音频文件名
            
        Returns:
            成功返回音频文件路径，失败返回 None
        """
        try:
            # 确保输出目录存在
            self.audio_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建完整的输出路径
            output_path = self.audio_dir / filename
            
            # 使用 gTTS 生成语音
            tts = gTTS(text=text, lang='zh-cn')
            tts.save(str(output_path))
            
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
            items: 包含文本和文件名的字典列表
            
        Returns:
            生成的音频文件路径列表
        """
        results = []
        for item in items:
            if 'text' in item and 'filename' in item:
                audio_path = self.generate_speech(item['text'], item['filename'])
                if audio_path:
                    results.append(str(audio_path))
        return results 