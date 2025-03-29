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
            "跳跃": lambda t: 1 + (np.sin(t * 2 * np.pi) * np.exp(-4 * t) * 0.3),  # 跳跃效果
            "随机": None  # 随机曲线标记，实际函数会在运行时确定
        }

        # 定义预设动画效果（不包含曲线相关描述，纯动画效果）
        self.preset_animations = {
            "静止": {
                "scale": [1.0, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "缩放-放大": {
                "scale": [1.0, 1.2],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "缩放-缩小": {
                "scale": [1.2, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "平移-左到右": {
                "scale": [1.0, 1.0],
                "position": [(-0.02, 0), (0.02, 0)],
                "curve": "线性"
            },
            "平移-右到左": {
                "scale": [1.0, 1.0],
                "position": [(0.02, 0), (-0.02, 0)],
                "curve": "线性"
            },
            "平移-上到下": {
                "scale": [1.0, 1.0],
                "position": [(0, -0.02), (0, 0.02)],
                "curve": "线性"
            },
            "平移-下到上": {
                "scale": [1.0, 1.0],
                "position": [(0, 0.02), (0, -0.02)],
                "curve": "线性"
            },
            "缩放+平移-左右": {
                "scale": [1.0, 1.1],
                "position": [(-0.02, 0), (0.02, 0)],
                "curve": "线性"
            },
            "缩放+平移-右左": {
                "scale": [1.0, 1.1],
                "position": [(0.02, 0), (-0.02, 0)],
                "curve": "线性"
            },
            "缩放+平移-上下": {
                "scale": [1.0, 1.1],
                "position": [(0, -0.02), (0, 0.02)],
                "curve": "线性"
            },
            "缩放+平移-下上": {
                "scale": [1.0, 1.1],
                "position": [(0, 0.02), (0, -0.02)],
                "curve": "线性"
            },
            "缩放+对角线-左上到右下": {
                "scale": [1.0, 1.15],
                "position": [(-0.015, -0.015), (0.015, 0.015)],
                "curve": "线性"
            },
            "缩放+对角线-右上到左下": {
                "scale": [1.0, 1.15],
                "position": [(0.015, -0.015), (-0.015, 0.015)],
                "curve": "线性"
            },
            "缩放+对角线-左下到右上": {
                "scale": [1.0, 1.15],
                "position": [(-0.015, 0.015), (0.015, -0.015)],
                "curve": "线性"
            },
            "缩放+对角线-右下到左上": {
                "scale": [1.0, 1.15],
                "position": [(0.015, 0.015), (-0.015, -0.015)],
                "curve": "线性"
            },
            "缩小+平移-左右": {
                "scale": [1.1, 1.0],
                "position": [(-0.02, 0), (0.02, 0)],
                "curve": "线性"
            },
            "缩小+平移-右左": {
                "scale": [1.1, 1.0],
                "position": [(0.02, 0), (-0.02, 0)],
                "curve": "线性"
            },
            "缩放-剧烈": {
                "scale": [1.0, 1.25],
                "position": [(0, 0), (0, 0)],
                "curve": "线性"
            },
            "跳动": {
                "scale": [1.0, 1.05],
                "position": [(0, 0.01), (0, -0.01)],
                "curve": "线性"
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
        if curve_name == "随机":
            # 当指定随机曲线时，随机选择一个曲线（除了"随机"本身）
            curve_options = list(self.curve_functions.keys())
            curve_options.remove("随机")
            selected_curve = random.choice(curve_options)
            print(f"随机选择曲线: '{selected_curve}'")
            return self.curve_functions[selected_curve]
            
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
        random_animation = self.preset_animations[random_preset].copy()
        
        # 随机选择一个曲线
        curve_options = list(self.curve_functions.keys())
        if None in curve_options:
            curve_options.remove(None)
        random_curve = random.choice(curve_options)
        
        random_animation['curve'] = random_curve
        print(f"随机选择动画: '{random_preset}' 搭配曲线: '{random_curve}'")
        
        return random_animation 