import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Optional, Union, Any
import random
import time
from moviepy.editor import ImageClip, VideoClip


class AnimationService:
    """
    专门处理图像动画的服务类，使用OpenCV实现高精度、无抖动的动画效果
    提供各种动画预设和平滑过渡
    """

    def __init__(self):
        """初始化动画服务"""
        # 默认帧率
        self.default_fps = 30

        # 定义动画曲线函数
        self.curve_functions = {
            "线性": lambda t: t,  # 线性曲线
            "缓入": lambda t: t**2,  # 缓入（慢开始，快结束）
            "缓出": lambda t: 1 - (1 - t)**2,  # 缓出（快开始，慢结束）
            "缓入缓出": lambda t: 3*(t**2) - 2*(t**3),  # 缓入缓出
            "回弹": lambda t: 1 + (1.7 * t - 1.7) * np.exp(-10 * t),  # 弹性回弹
            "急速": lambda t: t**3,  # 更强烈的缓入
            "强缓出": lambda t: 1 - (1 - t)**3,  # 更强烈的缓出
            "弹入": lambda t: 1 - np.cos(t * np.pi / 2),  # 弹性进入
            "弹出": lambda t: np.sin(t * np.pi / 2),  # 弹性退出
            "跳跃": lambda t: 1 + (np.sin(t * 2 * np.pi) * np.exp(-4 * t) * 0.3)  # 跳跃效果
        }

        # 定义预设动画效果
        self.preset_animations = {
            "静止": {
                "scale": [1.0, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "缩放-放大": {
                "scale": [1.0, 1.2],
                "position": [(0, 0), (0, 0)],
                "curve": "缓入"
            },
            "缩放-缩小": {
                "scale": [1.2, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "平移-左到右": {
                "scale": [1.0, 1.0],
                "position": [(-0.05, 0), (0.05, 0)],
                "curve": "缓入缓出"
            },
            "平移-右到左": {
                "scale": [1.0, 1.0],
                "position": [(0.05, 0), (-0.05, 0)],
                "curve": "缓入缓出"
            },
            "平移-上到下": {
                "scale": [1.0, 1.0],
                "position": [(0, -0.05), (0, 0.05)],
                "curve": "缓入缓出"
            },
            "平移-下到上": {
                "scale": [1.0, 1.0],
                "position": [(0, 0.05), (0, -0.05)],
                "curve": "缓入缓出"
            },
            "缩放+平移": {
                "scale": [1.0, 1.1],
                "position": [(0.03, 0), (-0.03, 0)],
                "curve": "缓入"
            },
            "慢速放大": {
                "scale": [0.9, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "缓出"
            },
            "弹性缩放": {
                "scale": [1.0, 1.15],
                "position": [(0, 0), (0, 0)],
                "curve": "回弹"
            },
            "跳动": {
                "scale": [1.0, 1.05],
                "position": [(0, 0.02), (0, -0.02)],
                "curve": "跳跃"
            }
        }

    def get_curve_function(self, curve_name: str) -> Callable[[float], float]:
        """
        获取指定名称的曲线函数
        
        Args:
            curve_name: 曲线名称
            
        Returns:
            曲线函数
        """
        return self.curve_functions.get(curve_name, self.curve_functions["线性"])

    def get_animation_settings(self, animation: Union[str, Dict]) -> Dict:
        """
        获取动画设置
        
        Args:
            animation: 动画名称或自定义设置
            
        Returns:
            动画设置字典
        """
        if isinstance(animation, str):
            if animation == "随机":
                return self.get_random_animation()
            else:
                return self.preset_animations.get(animation, self.preset_animations["静止"])
        return animation

    def get_random_animation(self) -> Dict:
        """
        获取随机动画设置
        
        Returns:
            随机选择的动画设置
        """
        # 随机选择一个预设动画（排除"静止"）
        preset_names = list(self.preset_animations.keys())
        if "静止" in preset_names:
            preset_names.remove("静止")
        
        random_preset = random.choice(preset_names)
        print(f"随机选择动画: '{random_preset}'")
        return self.preset_animations[random_preset] 