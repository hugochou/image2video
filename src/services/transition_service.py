import random
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple, Any, Union

from moviepy.editor import VideoClip, VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from moviepy.editor import AudioFileClip, TextClip, ColorClip
from moviepy.video.fx import all as vfx
from moviepy.video.compositing import transitions


class TransitionService:
    """管理视频转场效果的服务"""
    
    def __init__(self):
        """初始化转场服务"""
        # 定义所有可用的过渡效果
        self.transitions = {
            "无": "none",  # 特殊标记，表示无过渡效果
            "淡入淡出": transitions.crossfadein,
            "滑动-左": lambda clip, duration: transitions.slide_in(clip, duration, 'left'),
            "滑动-右": lambda clip, duration: transitions.slide_in(clip, duration, 'right'),
            "滑动-上": lambda clip, duration: transitions.slide_in(clip, duration, 'top'),
            "滑动-下": lambda clip, duration: transitions.slide_in(clip, duration, 'bottom'),
            "缩放淡入": lambda clip, duration: self._zoom_fadein(clip, duration),
            "旋转淡入": lambda clip, duration: self._rotate_fadein(clip, duration),
            "百叶窗": lambda clip, duration: self._blinds_effect(clip, duration),
            "扭曲溶解": lambda clip, duration: self._warp_dissolve(clip, duration),
            "闪白过渡": lambda clip, duration: self._flash_transition(clip, duration),
            "随机": "random"  # 特殊标记，表示随机选择一个效果
        }
    
    def apply_transition(self, clip: VideoClip, transition_name: str, duration: float) -> VideoClip:
        """
        应用指定的转场效果到视频片段
        
        Args:
            clip: 要应用效果的视频片段
            transition_name: 转场效果名称
            duration: 转场持续时间（秒）
            
        Returns:
            应用了转场效果的视频片段
        """
        if transition_name == "随机" or self.transitions.get(transition_name) == "random":
            # 随机选择一个转场效果
            transition_options = list(self.transitions.keys())
            transition_options.remove("随机")
            transition_options.remove("无")  # 确保不随机选到"无"
            selected_transition = random.choice(transition_options)
            transition_func = self.transitions.get(selected_transition)
            print(f"  随机选择转场: '{selected_transition}'")
            return self.apply_transition(clip, selected_transition, duration)
        elif transition_name == "无" or self.transitions.get(transition_name) == "none":
            # 不应用任何效果，直接返回原始片段
            print(f"  不应用转场效果")
            return clip
        else:
            # 获取转场函数并应用
            transition_func = self.transitions.get(transition_name)
            if transition_func and callable(transition_func):
                return transition_func(clip, duration)
            else:
                print(f"  警告: 未找到转场效果 '{transition_name}'，跳过应用转场")
                return clip
    
    def apply_transitions_to_clips(
        self, 
        clips: List[VideoClip], 
        transition: str = "淡入淡出", 
        transition_duration: float = 0.7,
        use_custom_transitions: bool = False,
        custom_transitions: List[str] = None
    ) -> List[VideoClip]:
        """
        将转场效果应用到一系列视频片段
        
        Args:
            clips: 视频片段列表
            transition: 全局转场效果
            transition_duration: 转场持续时间
            use_custom_transitions: 是否使用自定义转场
            custom_transitions: 自定义转场效果列表
            
        Returns:
            应用了转场效果的视频片段列表
        """
        if not clips:
            return []
            
        processed_clips = []
        
        for i, clip in enumerate(clips):
            if i == 0:
                # 第一个片段不需要过渡效果
                processed_clips.append(clip)
            else:
                # 确定当前片段的过渡效果
                current_transition_name = None
                
                if use_custom_transitions and custom_transitions and i-1 < len(custom_transitions):
                    # 使用自定义转场
                    current_transition_name = custom_transitions[i-1]
                    print(f"  片段 {i+1}: 使用自定义转场 '{current_transition_name}'")
                else:
                    # 使用全局转场
                    current_transition_name = transition
                    if transition != "随机" and transition != "无":
                        print(f"  片段 {i+1}: 使用转场 '{transition}'")
                
                # 应用转场效果
                processed_clip = self.apply_transition(clip, current_transition_name, transition_duration)
                processed_clips.append(processed_clip)
        
        return processed_clips
    
    # === 自定义转场效果 ===
    
    def _zoom_fadein(self, clip, duration):
        """缩放淡入效果"""
        def zoom_effect(get_frame, t):
            zoom = 0.5 + 0.5 * t / duration if t < duration else 1
            frame = get_frame(t)
            if t < duration:
                h, w = frame.shape[:2]
                center = (w/2, h/2)
                # 使用OpenCV创建缩放和平移矩阵
                M = np.float32([
                    [zoom, 0, center[0]*(1-zoom)],
                    [0, zoom, center[1]*(1-zoom)]
                ])
                frame = cv2.warpAffine(frame, M, (w, h))
                # 应用淡入效果
                alpha = t / duration
                frame = (frame * alpha).astype('uint8')
            return frame
        
        return clip.fl(lambda gf, t: zoom_effect(gf, t))
    
    def _rotate_fadein(self, clip, duration):
        """旋转淡入效果"""
        def rotate_effect(get_frame, t):
            angle = 90 * (1 - t / duration) if t < duration else 0
            frame = get_frame(t)
            if t < duration:
                h, w = frame.shape[:2]
                center = (w/2, h/2)
                rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
                frame = cv2.warpAffine(frame, rot_mat, (w, h))
                # 应用淡入效果
                alpha = t / duration
                frame = (frame * alpha).astype('uint8')
            return frame
        
        return clip.fl(lambda gf, t: rotate_effect(gf, t))
    
    def _blinds_effect(self, clip, duration):
        """百叶窗效果"""
        def blinds(get_frame, t):
            frame = get_frame(t)
            if t < duration:
                h, w = frame.shape[:2]
                progress = t / duration
                
                # 创建百叶窗效果
                num_blinds = 20
                result = np.zeros_like(frame)
                
                for i in range(num_blinds):
                    blind_height = h // num_blinds
                    y_start = i * blind_height
                    y_end = (i + 1) * blind_height
                    
                    # 控制每个百叶窗的开合程度
                    blind_progress = min(1, progress * 2 - i / num_blinds)
                    if blind_progress > 0:
                        result[y_start:y_end, :] = frame[y_start:y_end, :]
                        
                return result
            return frame
        
        return clip.fl(lambda gf, t: blinds(gf, t))
    
    def _warp_dissolve(self, clip, duration):
        """扭曲溶解效果"""
        def warp_effect(get_frame, t):
            frame = get_frame(t)
            if t < duration:
                h, w = frame.shape[:2]
                progress = t / duration
                
                # 创建扭曲网格
                map_x = np.zeros((h, w), np.float32)
                map_y = np.zeros((h, w), np.float32)
                
                for y in range(h):
                    for x in range(w):
                        # 添加基于时间的扭曲
                        offset_x = 10 * np.sin(y/30 + progress * 10) * (1 - progress)
                        offset_y = 10 * np.cos(x/30 + progress * 10) * (1 - progress)
                        
                        map_x[y, x] = x + offset_x
                        map_y[y, x] = y + offset_y
                
                # 应用扭曲和淡入
                warped = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
                result = cv2.addWeighted(np.zeros_like(frame), 1-progress, warped, progress, 0)
                return result
            return frame
        
        return clip.fl(lambda gf, t: warp_effect(gf, t))
    
    def _flash_transition(self, clip, duration):
        """闪白过渡效果"""
        def flash_effect(get_frame, t):
            frame = get_frame(t)
            if t < duration:
                progress = t / duration
                
                # 创建闪白效果
                if progress < 0.5:
                    # 前半部分：逐渐变白
                    white_intensity = progress * 2
                    result = cv2.addWeighted(
                        frame, 1 - white_intensity,
                        np.ones_like(frame) * 255, white_intensity,
                        0
                    )
                else:
                    # 后半部分：从白色回到正常
                    white_intensity = 2 - progress * 2
                    result = cv2.addWeighted(
                        frame, 1 - white_intensity,
                        np.ones_like(frame) * 255, white_intensity,
                        0
                    )
                
                return result
            return frame
        
        return clip.fl(lambda gf, t: flash_effect(gf, t)) 