import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Callable, Optional, Union
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

        # 定义动画曲线，增强缓入缓出效果
        self.animation_curves = {
            "线性": lambda x: x,
            "缓入": lambda x: x * x * x,  # 立方缓入，效果更强
            "强缓入": lambda x: x * x * x * x,  # 四次方缓入，效果更强烈
            "超强缓入": lambda x: x * x * x * x * x,  # 五次方缓入，效果最强
            "缓出": lambda x: 1 - (1 - x) * (1 - x) * (1 - x),  # 立方缓出，效果更强
            "强缓出": lambda x: 1 - (1 - x) * (1 - x) * (1 - x) * (1 - x),  # 四次方缓出，效果更强烈
            "超强缓出": lambda x: 1 - (1 - x) * (1 - x) * (1 - x) * (1 - x) * (1 - x),  # 五次方缓出，效果最强
            "缓入缓出": lambda x: 0.5 * (1 - np.cos(x * np.pi)),
            "强缓入缓出": lambda x: -(np.cos(np.pi * x) - 1) / 2,  # 与上面相同但更易读
            "弹性": lambda x: 0.8 * (-np.cos(x * np.pi * 2) * np.exp(-x * 3)) + x,  # 加强了反弹效果
            "回弹": lambda x: 2 * x * x if x < 0.5 else 1 - np.power(-2 * x + 2, 2) / 2  # 先加速后减速
        }

        # 定义预设动画（模拟摄像机运动）
        self.preset_animations = {
            "推": {  # 向前推进，画面逐渐放大
                "scale": [1.0, 1.2],
                "position": [(0, 0), (0, 0)],
                "curve": "缓入缓出"
            },
            "拉": {  # 向后拉远，画面逐渐缩小
                "scale": [1.2, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "缓入缓出"
            },
            "左移": {  # 摄像机左移
                "scale": [1.1, 1.1],
                "position": [(0.05, 0), (-0.05, 0)],
                "curve": "缓入缓出"
            },
            "右移": {  # 摄像机右移
                "scale": [1.1, 1.1],
                "position": [(-0.05, 0), (0.05, 0)],
                "curve": "缓入缓出"
            },
            "升": {  # 摄像机向上移动
                "scale": [1.1, 1.1],
                "position": [(0, 0.05), (0, -0.05)],
                "curve": "缓入缓出"
            },
            "降": {  # 摄像机向下移动
                "scale": [1.1, 1.1],
                "position": [(0, -0.05), (0, 0.05)],
                "curve": "缓入缓出"
            },
            "左遥": {  # 摄像机左平移同时缓慢放大
                "scale": [1.0, 1.15],
                "position": [(0.05, 0), (-0.05, 0)],
                "curve": "缓入缓出"
            },
            "右遥": {  # 摄像机右平移同时缓慢放大
                "scale": [1.0, 1.15],
                "position": [(-0.05, 0), (0.05, 0)],
                "curve": "缓入缓出"
            },
            "跟左": {  # 跟随左移动的主体
                "scale": [1.1, 1.1],
                "position": [(0.06, 0), (-0.06, 0)],
                "curve": "线性"
            },
            "跟右": {  # 跟随右移动的主体
                "scale": [1.1, 1.1],
                "position": [(-0.06, 0), (0.06, 0)],
                "curve": "线性"
            },
            "推左": {  # 推进同时左移
                "scale": [1.0, 1.2],
                "position": [(0.03, 0), (-0.03, 0)],
                "curve": "缓入缓出"
            },
            "推右": {  # 推进同时右移
                "scale": [1.0, 1.2],
                "position": [(-0.03, 0), (0.03, 0)],
                "curve": "缓入缓出"
            },
            "拉左": {  # 拉远同时左移
                "scale": [1.2, 1.0],
                "position": [(0.03, 0), (-0.03, 0)],
                "curve": "缓入缓出"
            },
            "拉右": {  # 拉远同时右移
                "scale": [1.2, 1.0],
                "position": [(-0.03, 0), (0.03, 0)],
                "curve": "缓入缓出"
            },
            "环绕": {  # 围绕主体环绕
                "scale": [1.1, 1.1],
                "position": [(-0.04, -0.04), (0.04, 0.04)],
                "curve": "缓入缓出"
            },
            "聚焦": {  # 逐渐放大并聚焦中心
                "scale": [1.0, 1.2],
                "position": [(0, 0), (0, 0)],
                "curve": "缓入"
            },
            "散焦": {  # 逐渐缩小远离主体
                "scale": [1.2, 1.0],
                "position": [(0, 0), (0, 0)],
                "curve": "缓出"
            },
            "随机": None  # 随机选择一个预设动画
        }

    def apply_animation(self, image_path: str, animation_settings: Dict, 
                       duration: float, canvas_size: Tuple[int, int] = None) -> VideoClip:
        """
        将动画效果应用到图像上，创建一个视频剪辑
        
        Args:
            image_path: 图像文件路径
            animation_settings: 动画设置字典或预设名称
            duration: 动画持续时间（秒）
            canvas_size: 画布尺寸 (宽, 高)，默认使用原图尺寸
            
        Returns:
            带有动画效果的视频剪辑
        """
        # 读取原始图像
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        # 将BGR转换为RGB（MoviePy使用RGB）
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 获取图像尺寸
        img_h, img_w = img.shape[:2]
        
        # 确定画布尺寸
        if canvas_size is None:
            canvas_size = (img_w, img_h)
        
        # 处理预设动画名称
        if isinstance(animation_settings, str):
            if animation_settings == "随机":
                preset_names = list(self.preset_animations.keys())
                preset_names.remove("随机")
                animation_settings = self.preset_animations[random.choice(preset_names)]
            else:
                animation_settings = self.preset_animations.get(animation_settings)
                if not animation_settings:
                    # 如果没有找到预设，创建静态图像
                    return self._create_static_clip(img_rgb, duration, canvas_size)
        
        # 如果没有提供动画设置，创建静态图像
        if not animation_settings:
            return self._create_static_clip(img_rgb, duration, canvas_size)
        
        # 提取动画参数
        scale_start, scale_end = animation_settings.get('scale', [1.0, 1.0])
        start_pos, end_pos = animation_settings.get('position', [(0, 0), (0, 0)])
        curve_name = animation_settings.get('curve', '线性')
        
        # 打印动画设置
        print(f"应用动画效果: {animation_settings}")
        curve_func = self.animation_curves.get(curve_name, self.animation_curves['线性'])
        
        # 打印曲线示例值，以便于调试
        print(f"曲线'{curve_name}'在不同时间点的值:")
        sample_points = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for p in sample_points:
            print(f"  t={p:.1f}, value={curve_func(p):.4f}")
            
        # 创建直接使用仿射变换的动画帧生成函数
        # 这种方法避免了离散采样导致的抖动
        def make_frame(t):
            # 计算当前时间的进度比例
            progress = t / duration if duration > 0 else 1.0
            
            # 使用指定曲线函数计算位移和缩放插值比例
            curve_progress = curve_func(progress)
            
            # 缩放也使用相同曲线（不再使用线性插值）
            current_scale = scale_start + (scale_end - scale_start) * curve_progress
            
            # 计算当前位置偏移（比例）
            current_pos_x = start_pos[0] + (end_pos[0] - start_pos[0]) * curve_progress
            current_pos_y = start_pos[1] + (end_pos[1] - start_pos[1]) * curve_progress
            
            # 每秒打印几次参数，用于调试
            if int(t * 10) % 5 == 0:
                print(f"t={t:.2f}, progress={progress:.4f}, curve_value={curve_progress:.4f}, scale={current_scale:.4f}")
            
            # 创建变换矩阵
            # 首先创建一个空白结果图像
            canvas_w, canvas_h = canvas_size
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            
            # 计算缩放和平移组合的变换矩阵
            # 1. 中心点偏移: canvas_center + offset
            center_x = canvas_w / 2
            center_y = canvas_h / 2
            
            # 2. 位移的像素值
            offset_x = canvas_w * current_pos_x
            offset_y = canvas_h * current_pos_y
            
            # 3. 组合变换: 将原始图像从中心缩放，然后平移到目标位置
            # OpenCV的getRotationMatrix2D可以同时处理缩放和旋转
            # 我们只需要缩放，所以角度设为0
            M = cv2.getRotationMatrix2D((img_w/2, img_h/2), 0, current_scale)
            
            # 添加平移部分
            M[0, 2] += center_x + offset_x - img_w/2 * current_scale
            M[1, 2] += center_y + offset_y - img_h/2 * current_scale
            
            # 应用变换矩阵 - 一步完成缩放和平移
            result = cv2.warpAffine(
                img_rgb, 
                M, 
                (canvas_w, canvas_h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0)
            )
            
            return result
        
        # 创建MoviePy视频剪辑
        video_clip = VideoClip(make_frame, duration=duration)
        return video_clip
    
    def _create_static_clip(self, img_rgb: np.ndarray, duration: float, 
                           canvas_size: Tuple[int, int]) -> VideoClip:
        """创建静态图像视频剪辑"""
        img_h, img_w = img_rgb.shape[:2]
        canvas_w, canvas_h = canvas_size
        
        # 如果图像尺寸与画布不同，将图像居中放置
        if img_w != canvas_w or img_h != canvas_h:
            # 创建居中放置图像的函数
            def make_frame(t):
                canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
                
                # 计算居中位置
                x_offset = max(0, (canvas_w - img_w) // 2)
                y_offset = max(0, (canvas_h - img_h) // 2)
                
                # 计算边界
                w = min(img_w, canvas_w)
                h = min(img_h, canvas_h)
                
                # 将图像放在画布中心
                canvas[y_offset:y_offset+h, x_offset:x_offset+w] = img_rgb[:h, :w]
                return canvas
        else:
            # 尺寸一致，直接使用原图
            def make_frame(t):
                return img_rgb
        
        # 创建VideoClip
        return VideoClip(make_frame, duration=duration) 