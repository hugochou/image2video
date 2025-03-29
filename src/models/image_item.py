from dataclasses import dataclass
from typing import Optional, Dict
from pathlib import Path

@dataclass
class ImageItem:
    id: str
    image_path: Path
    text: str = ""
    audio_path: Optional[Path] = None
    duration: float = 5.0  # 默认显示时间
    animation: Optional[Dict] = None  # 动画设置
    order: int = 0
    
    def __post_init__(self):
        if isinstance(self.image_path, str):
            self.image_path = Path(self.image_path)
        if self.audio_path and isinstance(self.audio_path, str):
            self.audio_path = Path(self.audio_path)
    
    @property
    def has_audio(self) -> bool:
        return self.audio_path is not None and self.audio_path.exists()
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'image_path': self.image_path,
            'text': self.text,
            'audio_path': self.audio_path,
            'duration': self.duration,
            'animation': self.animation,
            'order': self.order
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageItem':
        return cls(
            id=data['id'],
            image_path=data['image_path'],
            text=data['text'],
            audio_path=data.get('audio_path'),
            duration=data.get('duration', 5.0),
            animation=data.get('animation'),
            order=data.get('order', 0)
        ) 