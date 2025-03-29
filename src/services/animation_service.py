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
            "强缓入": lambda t: t**3,  # 更强烈的缓入
            "强缓出": lambda t: 1 - (1 - t)**3,  # 更强烈的缓出
            "平滑弹入": lambda t: 1 - np.cos(t * np.pi / 2),  # 平滑弹性进入
            "平滑弹出": lambda t: np.sin(t * np.pi / 2),  # 平滑弹性退出
            "随机": None  # 随机曲线标记，实际函数会在运行时确定
        }

        # 缩放预设选项
        self.scale_presets = {
            "无": [1.0, 1.0],
            "放大": [1.0, 1.2],
            "缩小": [1.2, 1.0],
            "轻微放大": [1.0, 1.1],
            "轻微缩小": [1.1, 1.0],
            "剧烈放大": [1.0, 1.25],
            "脉动": [1.0, 1.05],
            "随机": None  # 随机标记，实际值会在运行时确定
        }
        
        # 平移预设选项
        self.position_presets = {
            "无": [(0, 0), (0, 0)],
            "左到右": [(-0.02, 0), (0.02, 0)],
            "右到左": [(0.02, 0), (-0.02, 0)],
            "上到下": [(0, -0.02), (0, 0.02)],
            "下到上": [(0, 0.02), (0, -0.02)],
            "左上到右下": [(-0.015, -0.015), (0.015, 0.015)],
            "右上到左下": [(0.015, -0.015), (-0.015, 0.015)],
            "左下到右上": [(-0.015, 0.015), (0.015, -0.015)],
            "右下到左上": [(0.015, 0.015), (-0.015, -0.015)],
            "轻微左右": [(-0.01, 0), (0.01, 0)],
            "轻微上下": [(0, -0.01), (0, 0.01)],
            "随机": None  # 随机标记，实际值会在运行时确定
        }

        # 定义预设动画效果（兼容原有代码）
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
            return self.preset_animations.get(animation, self.preset_animations["静止"])
        return animation

    def get_random_scale(self) -> List:
        """获取随机缩放设置"""
        scale_options = list(self.scale_presets.keys())
        scale_options.remove("无")
        if "随机" in scale_options:
            scale_options.remove("随机")
        
        random_scale_name = random.choice(scale_options)
        random_scale = self.scale_presets[random_scale_name]
        print(f"随机选择缩放效果: '{random_scale_name}' -> 值={random_scale}")
        return random_scale
    
    def get_random_position(self) -> List:
        """获取随机位移设置"""
        position_options = list(self.position_presets.keys())
        position_options.remove("无")
        if "随机" in position_options:
            position_options.remove("随机")
        
        random_position_name = random.choice(position_options)
        random_position = self.position_presets[random_position_name]
        print(f"随机选择位移效果: '{random_position_name}' -> 值={random_position}")
        return random_position
    
    def combine_animation_settings(self, scale_preset: str, position_preset: str, curve: str) -> Dict:
        """
        组合缩放和位移预设，创建完整的动画设置
        
        Args:
            scale_preset: 缩放预设名称
            position_preset: 位移预设名称
            curve: 曲线名称
        
        Returns:
            组合后的动画设置字典
        """
        print(f"\n===== 动画参数 =====")
        print(f"缩放预设: '{scale_preset}'")
        print(f"平移预设: '{position_preset}'")
        print(f"曲线函数: '{curve}'")
        
        # 处理缩放预设
        if scale_preset == "随机":
            scale = self.get_random_scale()
        else:
            scale = self.scale_presets.get(scale_preset, self.scale_presets["无"])
        
        # 处理位移预设
        if position_preset == "随机":
            position = self.get_random_position()
        else:
            position = self.position_presets.get(position_preset, self.position_presets["无"])
        
        # 创建组合设置
        animation_settings = {
            "scale": scale,
            "position": position,
            "curve": curve
        }
        
        print(f"缩放参数: 起始={scale[0]:.2f}, 结束={scale[1]:.2f}")
        print(f"平移参数: 起始=({position[0][0]:.3f}, {position[0][1]:.3f}), 结束=({position[1][0]:.3f}, {position[1][1]:.3f})")
        print(f"====== 结束 ======\n")
        
        return animation_settings 