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
            "淡入淡出": self._crossfade,
            "滑动-左": lambda clip1, clip2, duration: self._slide_in(clip1, clip2, duration, 'left'),
            "滑动-右": lambda clip1, clip2, duration: self._slide_in(clip1, clip2, duration, 'right'),
            "滑动-上": lambda clip1, clip2, duration: self._slide_in(clip1, clip2, duration, 'top'),
            "滑动-下": lambda clip1, clip2, duration: self._slide_in(clip1, clip2, duration, 'bottom'),
            "缩放淡入": lambda clip1, clip2, duration: self._zoom_fade(clip1, clip2, duration),
            "旋转淡入": lambda clip1, clip2, duration: self._rotate_fade(clip1, clip2, duration),
            "百叶窗": lambda clip1, clip2, duration: self._blinds_effect(clip1, clip2, duration),
            "扭曲溶解": lambda clip1, clip2, duration: self._warp_dissolve(clip1, clip2, duration),
            "闪白过渡": lambda clip1, clip2, duration: self._flash_transition(clip1, clip2, duration),
            "随机": None  # 随机转场标记，实际函数会在运行时确定
        }
    
    def get_transition_function(self, transition_name: str):
        """
        获取指定名称的转场函数
        
        Args:
            transition_name: 转场效果名称
            
        Returns:
            转场函数
        """
        if transition_name == "随机":
            # 当指定随机转场时，随机选择一个转场效果（除了"无"和"随机"本身）
            transition_options = list(self.transitions.keys())
            if "无" in transition_options:
                transition_options.remove("无")
            if "随机" in transition_options:
                transition_options.remove("随机")
            
            selected_transition = random.choice(transition_options)
            print(f"随机选择转场效果: '{selected_transition}'")
            return self.transitions[selected_transition]
            
        return self.transitions.get(transition_name, self._no_transition)
    
    def apply_transitions_to_clips(
        self, 
        clips: List[VideoClip], 
        transition_name: str, 
        transition_duration: float,
        use_custom_transitions: bool = False,
        custom_transitions: List[str] = None
    ) -> List[VideoClip]:
        """
        将转场效果应用到一系列视频片段，并返回一个新的片段列表
        
        Args:
            clips: 视频片段列表
            transition_name: 转场效果名称
            transition_duration: 转场持续时间
            use_custom_transitions: 是否使用自定义转场
            custom_transitions: 自定义转场效果列表
            
        Returns:
            应用了转场效果的视频片段列表
        """
        if not clips or len(clips) < 2:
            return clips
        
        # 存储原始片段，避免修改输入参数
        result_clips = clips.copy()
        
        # 如果使用自定义转场，并且提供了足够的转场效果
        if use_custom_transitions and custom_transitions:
            print("使用自定义转场效果序列")
            # 确保有足够的转场效果（需要比片段数少1个）
            if len(custom_transitions) < len(clips) - 1:
                # 不够的部分用默认转场补充
                missing = len(clips) - 1 - len(custom_transitions)
                custom_transitions.extend([transition_name] * missing)
                print(f"  自定义转场数量不足，添加 {missing} 个默认转场")
            
            # 依次处理每个转场点
            for i in range(1, len(clips)):
                prev_clip = clips[i-1]
                curr_clip = clips[i]
                trans_name = custom_transitions[i-1]
                
                print(f"  应用转场 {i}/{len(clips)-1}: '{trans_name}'")
                
                # 应用转场效果
                if trans_name != "无" and self.transitions.get(trans_name) != "none":
                    # 获取转场函数
                    if trans_name == "随机":
                        # 随机选择一个转场效果
                        trans_func = self.get_transition_function(trans_name)
                    else:
                        trans_func = self.transitions.get(trans_name)
                    
                    # 如果找到了有效的转场函数
                    if callable(trans_func):
                        # 创建带有转场的片段
                        trans_clip = trans_func(prev_clip, curr_clip, transition_duration)
                        # 替换当前片段
                        result_clips[i] = trans_clip
        else:
            # 使用全局转场效果
            print(f"使用全局转场效果: '{transition_name}'")
            
            # 如果是"无"转场，直接返回原始片段
            if transition_name == "无" or self.transitions.get(transition_name) == "none":
                print("  不应用任何转场效果")
                return result_clips
            
            # 如果是随机转场，为每个连接点随机选择不同的转场
            if transition_name == "随机" or self.transitions.get(transition_name) == "random":
                print("  为每个连接点随机选择转场效果")
                for i in range(1, len(clips)):
                    # 随机选择一个转场效果
                    trans_func = self.get_transition_function(transition_name)
                    
                    print(f"  片段 {i+1}: 随机选择转场 '{transition_name}'")
                    
                    # 应用随机选择的转场
                    if callable(trans_func):
                        trans_clip = trans_func(clips[i-1], clips[i], transition_duration)
                        result_clips[i] = trans_clip
            else:
                # 对所有连接点应用相同的转场
                trans_func = self.transitions.get(transition_name)
                if callable(trans_func):
                    for i in range(1, len(clips)):
                        print(f"  应用转场到片段 {i+1}/{len(clips)}")
                        trans_clip = trans_func(clips[i-1], clips[i], transition_duration)
                        result_clips[i] = trans_clip
        
        return result_clips
    
    def create_composite_transition(self, clips: List[VideoClip], transition_name: str, duration: float, custom_transitions: List[str] = None) -> VideoClip:
        """
        创建一个包含所有片段和转场效果的合成视频
        
        Args:
            clips: 视频片段列表
            transition_name: 默认转场效果名称
            duration: 转场持续时间
            custom_transitions: 自定义转场效果列表（如果提供）
            
        Returns:
            包含所有片段和转场的合成视频
        """
        if not clips:
            raise ValueError("没有提供任何视频片段")
        
        if len(clips) == 1:
            return clips[0]
        
        # 创建最终片段列表
        final_clips = [clips[0]]  # 第一个片段直接添加，不需要转场
        
        # 为其余每个片段创建转场
        for i in range(1, len(clips)):
            current_transition = transition_name
            
            # 如果有自定义转场，并且数量足够，使用自定义转场
            if custom_transitions and i-1 < len(custom_transitions):
                current_transition = custom_transitions[i-1]
                print(f"  片段 {i+1}: 使用自定义转场 '{current_transition}'")
            
            # 获取前一个片段和当前片段
            prev_clip = clips[i-1]
            curr_clip = clips[i]
            
            # 处理特殊转场类型
            if current_transition == "无" or self.transitions.get(current_transition) == "none":
                # 无转场，直接添加
                final_clips.append(curr_clip)
                continue
            
            # 处理随机转场
            if current_transition == "随机" or self.transitions.get(current_transition) == "random":
                # 随机选择一个转场效果
                trans_func = self.get_transition_function(current_transition)
            
            # 获取转场函数
            transition_func = self.transitions.get(current_transition)
            
            # 如果找到了有效的转场函数
            if callable(transition_func):
                # 创建转场片段
                transition_clip = transition_func(prev_clip, curr_clip, duration)
                # 添加到最终列表
                final_clips.append(transition_clip)
            else:
                # 如果找不到有效的转场函数，使用默认的交叉淡入淡出
                print(f"  警告: 未找到转场效果 '{current_transition}'，使用默认淡入淡出")
                transition_clip = self._crossfade(prev_clip, curr_clip, duration)
                final_clips.append(transition_clip)
        
        # 连接所有片段，保留音频
        final_clip = concatenate_videoclips(final_clips, method="compose")
        
        return final_clip
    
    # === 转场效果实现 ===
    
    def _crossfade(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        交叉淡入淡出效果
        从clip1平滑过渡到clip2
        """
        # 定义淡入淡出效果函数
        def crossfade_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                # 使用OpenCV的addWeighted进行帧混合
                result = cv2.addWeighted(frame1, 1-progress, frame2, progress, 0)
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: crossfade_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _slide_in(self, clip1: VideoClip, clip2: VideoClip, duration: float, direction: str = 'left') -> VideoClip:
        """
        滑入效果
        从clip1平滑过渡到clip2，clip2从指定方向滑入
        
        Args:
            clip1: 前一个视频片段
            clip2: 当前视频片段
            duration: 转场持续时间
            direction: 滑入方向 ('left', 'right', 'top', 'bottom')
            
        Returns:
            包含转场效果的视频片段
        """
        # 定义滑动函数
        def slide_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                h, w = frame1.shape[:2]
                result = frame1.copy()
                
                # 计算滑动偏移
                if direction == 'left':
                    offset_x = int(w * (1 - progress))
                    frame2_visible = frame2[:, :max(0, w-offset_x)]
                    result[:, offset_x:] = frame2_visible
                elif direction == 'right':
                    offset_x = int(w * (1 - progress))
                    frame2_visible = frame2[:, offset_x:]
                    result[:, :min(w, w-offset_x)] = frame2_visible
                elif direction == 'top':
                    offset_y = int(h * (1 - progress))
                    frame2_visible = frame2[:max(0, h-offset_y), :]
                    result[offset_y:, :] = frame2_visible
                elif direction == 'bottom':
                    offset_y = int(h * (1 - progress))
                    frame2_visible = frame2[offset_y:, :]
                    result[:min(h, h-offset_y), :] = frame2_visible
                
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: slide_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _zoom_fade(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        缩放淡入效果
        从clip1平滑过渡到clip2，clip2从小到大缩放进入
        """
        # 定义缩放函数
        def zoom_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                # 对第二个帧应用缩放
                h, w = frame2.shape[:2]
                center = (w/2, h/2)
                zoom_factor = 0.5 + 0.5 * progress
                
                # 创建缩放矩阵
                M = np.float32([
                    [zoom_factor, 0, center[0]*(1-zoom_factor)],
                    [0, zoom_factor, center[1]*(1-zoom_factor)]
                ])
                zoomed_frame2 = cv2.warpAffine(frame2, M, (w, h))
                
                # 根据进度混合两个帧
                result = cv2.addWeighted(frame1, 1-progress, zoomed_frame2, progress, 0)
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: zoom_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _rotate_fade(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        旋转淡入效果
        从clip1平滑过渡到clip2，clip2旋转进入
        """
        # 定义旋转函数
        def rotate_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                # 对第二个帧应用旋转
                h, w = frame2.shape[:2]
                center = (w/2, h/2)
                angle = 90 * (1 - progress)
                
                rot_mat = cv2.getRotationMatrix2D(center, angle, progress)
                rotated_frame2 = cv2.warpAffine(frame2, rot_mat, (w, h))
                
                # 根据进度混合两个帧
                result = cv2.addWeighted(frame1, 1-progress, rotated_frame2, progress, 0)
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: rotate_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _blinds_effect(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        百叶窗效果
        从clip1平滑过渡到clip2，模拟百叶窗打开效果
        """
        # 定义百叶窗效果函数
        def blinds_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                h, w = frame1.shape[:2]
                result = frame1.copy()
                
                # 创建百叶窗效果
                num_blinds = 20
                blind_height = h // num_blinds
                
                for i in range(num_blinds):
                    y_start = i * blind_height
                    y_end = min((i + 1) * blind_height, h)
                    
                    # 控制每个百叶窗的开合程度
                    blind_progress = min(1, progress * 2 - i / num_blinds)
                    if blind_progress > 0:
                        # 只替换当前百叶窗部分
                        result[y_start:y_end, :] = cv2.addWeighted(
                            frame1[y_start:y_end, :], 1-blind_progress,
                            frame2[y_start:y_end, :], blind_progress,
                            0
                        )
                
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: blinds_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _warp_dissolve(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        扭曲溶解效果
        从clip1平滑过渡到clip2，带有扭曲效果
        """
        # 定义扭曲溶解函数
        def warp_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧并应用扭曲效果
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                h, w = frame1.shape[:2]
                
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
                
                # 分别对两个帧应用扭曲
                warped1 = cv2.remap(frame1, map_x, map_y, cv2.INTER_LINEAR)
                warped2 = frame2  # 新帧不扭曲
                
                # 根据进度混合两个帧
                result = cv2.addWeighted(warped1, 1-progress, warped2, progress, 0)
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: warp_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _flash_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """
        闪白过渡效果
        从clip1过渡到clip2，中间经过白色闪光
        """
        # 定义闪白效果函数
        def flash_effect(get_frame, t):
            # 如果在转场区域内
            if t < duration:
                progress = t / duration
                
                # 获取前一个片段的最后一帧和当前片段的第一帧
                frame1 = clip1.get_frame(clip1.duration - duration + t)
                frame2 = clip2.get_frame(t)
                
                # 创建闪白效果
                if progress < 0.5:
                    # 前半部分：前一帧逐渐变白
                    white_intensity = progress * 2
                    result = cv2.addWeighted(
                        frame1, 1 - white_intensity,
                        np.ones_like(frame1) * 255, white_intensity,
                        0
                    )
                else:
                    # 后半部分：从白色过渡到新帧
                    white_intensity = 2 - progress * 2
                    result = cv2.addWeighted(
                        frame2, 1 - white_intensity,
                        np.ones_like(frame2) * 255, white_intensity,
                        0
                    )
                
                return result
            else:
                # 转场结束后直接返回当前帧
                return clip2.get_frame(t)
        
        # 创建新片段
        new_clip = VideoClip(
            lambda t: flash_effect(None, t),
            duration=clip2.duration
        )
        
        # 复制原始片段的音频
        if clip2.audio is not None:
            new_clip = new_clip.set_audio(clip2.audio)
        
        return new_clip
    
    def _no_transition(self, clip1: VideoClip, clip2: VideoClip, duration: float) -> VideoClip:
        """无转场效果"""
        return clip2 