from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QTextEdit,
                             QFileDialog, QMessageBox, QProgressDialog,
                             QGridLayout, QFrame, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QGroupBox, QFormLayout, QComboBox,
                             QInputDialog, QSlider, QApplication, QDialog,
                             QDialogButtonBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from pathlib import Path
import uuid
from typing import List, Dict
import platform
import os
import subprocess
import json
import time

from ..models.image_item import ImageItem
from ..services.audio_service import AudioService
from ..services.video_service import VideoService

class AudioGenerationThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, items: List[ImageItem], audio_service: AudioService):
        super().__init__()
        self.items = items
        self.audio_service = audio_service
    
    def run(self):
        try:
            # 生成语音
            for i, item in enumerate(self.items):
                if not item.text.strip():
                    continue
                    
                try:
                    # 生成音频文件
                    audio_path = self.audio_service.generate_speech(
                        item.text,
                        f"{item.id}.mp3"
                    )
                    if audio_path:
                        item.audio_path = audio_path
                        self.progress.emit(i + 1)
                except Exception as e:
                    print(f"生成语音失败: {str(e)}")
                    continue
            
            self.finished.emit(True)
        except Exception as e:
            print(f"生成语音时出错: {str(e)}")
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image2Video")
        self.setMinimumSize(1200, 800)
        
        # 初始化数据
        self.image_items: List[ImageItem] = []
        self.audio_service = AudioService()
        self.video_service = VideoService()
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        layout = QVBoxLayout(main_widget)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        
        # 添加图片按钮
        add_button = QPushButton("添加图片")
        add_button.clicked.connect(self.add_images)
        button_layout.addWidget(add_button)
        
        # 生成语音按钮
        generate_audio_button = QPushButton("生成语音")
        generate_audio_button.clicked.connect(self.generate_audio)
        button_layout.addWidget(generate_audio_button)
        
        # 生成视频按钮
        generate_video_button = QPushButton("生成视频")
        generate_video_button.clicked.connect(self.generate_video)
        button_layout.addWidget(generate_video_button)
        
        # 预览视频按钮
        self.preview_button = QPushButton("预览视频")
        self.preview_button.clicked.connect(self.preview_video)
        self.preview_button.setEnabled(False)
        button_layout.addWidget(self.preview_button)
        
        layout.addLayout(button_layout)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 创建内容容器
        self.content_widget = QWidget()
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setColumnStretch(0, 2)  # 图片列
        self.content_layout.setColumnStretch(1, 2)  # 文本列
        self.content_layout.setColumnStretch(2, 1)  # 试听列
        self.content_layout.setColumnStretch(3, 1)  # 生成片段列
        self.content_layout.setColumnStretch(4, 2)  # 动画设置列
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def add_images(self):
        """添加图片"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if files:
            for file in files:
                item = ImageItem(
                    id=str(uuid.uuid4()),
                    image_path=Path(file),
                    text=""
                )
                self.image_items.append(item)
                self.add_item_to_grid(item)
            
            self.statusBar().showMessage(f"已添加 {len(files)} 张图片")
    
    def add_item_to_grid(self, item: ImageItem, row: int = None):
        """添加项目到网格布局"""
        if row is None:
            row = self.content_layout.rowCount()
        
        # 图片名称和预览
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        
        # 图片名称
        name_label = QLabel(item.image_path.name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(name_label)
        
        # 图片预览
        image_label = QLabel()
        pixmap = QPixmap(str(item.image_path))
        scaled_pixmap = pixmap.scaled(200, 150, Qt.AspectRatioMode.KeepAspectRatio)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(image_label)
        
        self.content_layout.addWidget(image_container, row, 0)
        
        # 文本输入
        text_edit = QTextEdit()
        text_edit.setPlainText(item.text)
        text_edit.textChanged.connect(lambda: self.on_text_changed(item, text_edit))
        self.content_layout.addWidget(text_edit, row, 1)
        
        # 试听按钮
        preview_button = QPushButton("试听")
        preview_button.setEnabled(False)
        preview_button.clicked.connect(lambda: self.preview_audio(item))
        self.content_layout.addWidget(preview_button, row, 2)
        
        # 生成片段按钮
        generate_clip_button = QPushButton("生成片段")
        generate_clip_button.clicked.connect(lambda: self.generate_clip(item))
        self.content_layout.addWidget(generate_clip_button, row, 3)
        
        # 动画设置
        animation_widget = self.create_animation_settings(item)
        animation_widget.setEnabled(True)
        animation_widget.setStyleSheet("QGroupBox { border: 1px solid #ccc; }")
        self.content_layout.addWidget(animation_widget, row, 4)
    
    def on_text_changed(self, item: ImageItem, text_edit: QTextEdit):
        """文本变化时更新"""
        item.text = text_edit.toPlainText()
    
    def generate_audio(self):
        """生成语音"""
        if not self.image_items:
            QMessageBox.warning(self, "警告", "请先添加图片")
            return
        
        # 创建音频生成线程
        self.audio_thread = AudioGenerationThread(self.image_items, self.audio_service)
        self.audio_thread.finished.connect(self.on_audio_generation_finished)
        self.audio_thread.error.connect(self.on_audio_generation_finished)  # 修改为正确的函数名
        self.audio_thread.progress.connect(self.on_audio_generation_progress)
        
        # 创建进度对话框
        self.progress_dialog = QProgressDialog("正在生成语音...", "取消", 0, len(self.image_items), self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.canceled.connect(self.audio_thread.terminate)
        self.progress_dialog.show()
        
        # 开始生成
        self.audio_thread.start()
    
    def on_audio_generation_finished(self, success: bool = True):
        """音频生成完成的回调"""
        if success:
            self.statusBar().showMessage("语音生成完成")
            # 更新界面
            for row in range(1, self.content_layout.rowCount()):
                item = self.image_items[row - 1]
                if item.has_audio:
                    # 启用试听按钮
                    preview_button = self.content_layout.itemAtPosition(row, 2).widget()
                    preview_button.setEnabled(True)
        else:
            QMessageBox.warning(self, "错误", "语音生成失败")
        
        self.progress_dialog.close()
    
    def on_audio_generation_progress(self, value: int):
        """音频生成进度的回调"""
        self.progress_dialog.setValue(value)
    
    def preview_audio(self, item: ImageItem):
        """预览音频"""
        if item.has_audio:
            self.audio_service.preview_audio(item.audio_path)
    
    def generate_video(self):
        """生成完整视频"""
        if not self.image_items:
            QMessageBox.warning(self, "提示", "请先添加图片")
            return
            
        # 高级设置对话框
        dialog = VideoSettingsDialog(self, self.video_service)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # 获取设置
        settings = dialog.get_settings()
        
        # 在状态栏显示处理中消息，不使用弹窗
        self.statusBar().showMessage("正在生成视频，请稍候...")
        
        # 禁用相关按钮，防止用户在处理过程中进行操作
        self.disable_ui_during_processing(True)
        
        try:
            # 创建输出目录
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # 生成视频
            output_path = self.video_service.create_video(
                [item.to_dict() for item in self.image_items],
                str(output_dir / "final_video.mp4"),
                settings["transition"],
                settings["transition_duration"],
                {
                    "use_custom_transitions": settings["use_custom_transitions"],
                    "custom_transitions": settings["custom_transitions"],
                    "video_resolution": settings["video_resolution"],
                    "output_quality": settings["output_quality"]
                }
            )
            
            if output_path:
                self.last_video_path = output_path
                self.preview_button.setEnabled(True)
                
                # 更新状态栏显示完成消息
                self.statusBar().showMessage(f"视频已成功生成：{output_path}")
                
                # 询问是否立即预览
                reply = QMessageBox.question(
                    self,
                    "视频已生成",
                    f"视频已成功生成，是否立即播放？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.preview_video()
                
        except Exception as e:
            # 显示错误消息
            self.statusBar().showMessage(f"生成视频失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"生成视频失败: {str(e)}")
        finally:
            # 恢复UI状态
            self.disable_ui_during_processing(False)
    
    def disable_ui_during_processing(self, disabled: bool):
        """在处理过程中禁用UI元素"""
        # 禁用/启用主要操作按钮
        for button in self.findChildren(QPushButton):
            if button.text() in ["添加图片", "生成语音", "生成视频"]:
                button.setEnabled(not disabled)
                
        # 可以根据需要禁用其他UI元素
    
    def preview_video(self):
        """预览已生成的视频"""
        if hasattr(self, 'last_video_path') and self.last_video_path:
            self.video_service.open_with_default_player(self.last_video_path)
        else:
            QMessageBox.information(self, "提示", "还没有生成视频")
    
    def generate_clip(self, item: ImageItem):
        """生成单个片段"""
        # 如果没有动画设置，则随机选择一个预设
        if not hasattr(item, 'animation') or not item.animation:
            # 获取当前行的动画设置组件
            row = self.image_items.index(item) + 1
            animation_widget = self.content_layout.itemAtPosition(row, 4).widget()
            
            # 随机选择缩放和平移预设
            scale_combo = animation_widget.findChild(QComboBox, "scale_combo")
            position_combo = animation_widget.findChild(QComboBox, "position_combo")
            
            # 设置为随机
            scale_combo.setCurrentText("随机")
            position_combo.setCurrentText("随机")
            
            # 更新动画设置
            curve_combo = animation_widget.findChild(QComboBox, "curve_combo")
            animation_settings = self.video_service.animation_service.combine_animation_settings(
                "随机", "随机", curve_combo.currentText()
            )
            item.animation = animation_settings
        
        # 获取当前行以便访问动画控件
        row = self.image_items.index(item) + 1
        animation_widget = self.content_layout.itemAtPosition(row, 4).widget()
        
        # 获取预览需要的所有控件
        scale_combo = animation_widget.findChild(QComboBox, "scale_combo")
        position_combo = animation_widget.findChild(QComboBox, "position_combo")
        curve_combo = animation_widget.findChild(QComboBox, "curve_combo")
        
        # 更新动画设置 - 组合缩放、平移和曲线
        scale_preset = scale_combo.currentText()
        position_preset = position_combo.currentText()
        curve_name = curve_combo.currentText()
        
        # 组合设置
        animation_settings = self.video_service.animation_service.combine_animation_settings(
            scale_preset, position_preset, curve_name
        )
        
        # 应用到item
        item.animation = animation_settings
        
        # 生成预览文件
        output_path = self.video_service.preview_clip(
            item.to_dict(),
            f"preview_{item.id}.mp4"
        )
        
        # 预览视频
        self.video_service.open_with_default_player(output_path)

    def create_animation_settings(self, item: ImageItem) -> QWidget:
        """
        创建动画设置控件
        包含缩放选择、平移选择和曲线选择，分别可以组合使用
        """
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 缩放预设选择
        scale_layout = QHBoxLayout()
        scale_layout.setContentsMargins(0, 0, 0, 0)
        
        scale_combo = QComboBox()
        scale_combo.setObjectName("scale_combo")
        scale_combo.addItems(list(self.video_service.animation_service.scale_presets.keys()))
        
        scale_label = QLabel("缩放:")
        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(scale_combo, 1)
        
        # 平移预设选择
        position_layout = QHBoxLayout()
        position_layout.setContentsMargins(0, 0, 0, 0)
        
        position_combo = QComboBox()
        position_combo.setObjectName("position_combo")
        position_combo.addItems(list(self.video_service.animation_service.position_presets.keys()))
        
        position_label = QLabel("平移:")
        position_layout.addWidget(position_label)
        position_layout.addWidget(position_combo, 1)
        
        # 曲线选择
        curve_layout = QHBoxLayout()
        curve_layout.setContentsMargins(0, 0, 0, 0)
        
        curve_combo = QComboBox()
        curve_combo.setObjectName("curve_combo")
        curve_combo.addItems(self.video_service.animation_service.curve_functions.keys())
        
        # 初始化曲线选择为"缓入缓出"
        curve_combo.setCurrentText("随机")
        
        curve_label = QLabel("曲线:")
        curve_layout.addWidget(curve_label)
        curve_layout.addWidget(curve_combo, 1)
        
        # 预览按钮
        preview_layout = QHBoxLayout()
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_button = QPushButton("预览")
        preview_button.setObjectName("preview_button")
        preview_button.clicked.connect(lambda: self.preview_animation(item))
        preview_layout.addStretch()
        preview_layout.addWidget(preview_button)
        
        # 添加所有布局到主布局
        main_layout.addLayout(scale_layout)
        main_layout.addLayout(position_layout)
        main_layout.addLayout(curve_layout)
        main_layout.addLayout(preview_layout)
        
        # 设置初始默认值为随机
        scale_combo.setCurrentText("随机")
        position_combo.setCurrentText("随机")
        
        # 设置初始值（如果有）
        if hasattr(item, 'animation') and item.animation:
            if isinstance(item.animation, str):
                if item.animation == "随机":
                    scale_combo.setCurrentText("随机")
                    position_combo.setCurrentText("随机")
            elif isinstance(item.animation, dict):
                # 尝试匹配缩放设置
                scale_value = item.animation.get('scale', [1.0, 1.0])
                position_value = item.animation.get('position', [(0, 0), (0, 0)])
                curve_value = item.animation.get('curve', "缓入缓出")
                
                # 设置曲线值
                if curve_value in self.video_service.animation_service.curve_functions:
                    curve_combo.setCurrentText(curve_value)
                
                # 查找匹配的缩放预设
                scale_found = False
                for scale_name, scale_preset in self.video_service.animation_service.scale_presets.items():
                    if scale_name != "随机" and scale_preset == scale_value:
                        scale_combo.setCurrentText(scale_name)
                        scale_found = True
                        break
                
                if not scale_found:
                    # 如果没有找到匹配的缩放预设，设为"无"
                    scale_combo.setCurrentText("无")
                
                # 查找匹配的平移预设
                position_found = False
                for position_name, position_preset in self.video_service.animation_service.position_presets.items():
                    if position_name != "随机" and position_preset == position_value:
                        position_combo.setCurrentText(position_name)
                        position_found = True
                        break
                
                if not position_found:
                    # 如果没有找到匹配的平移预设，设为"无"
                    position_combo.setCurrentText("无")
        
        # 连接信号
        def update_animation():
            # 获取当前选择的预设
            scale_preset = scale_combo.currentText()
            position_preset = position_combo.currentText()
            curve_name = curve_combo.currentText()
            
            # 组合设置
            animation_settings = self.video_service.animation_service.combine_animation_settings(
                scale_preset, position_preset, curve_name
            )
            
            # 应用到item
            item.animation = animation_settings
        
        # 连接信号
        scale_combo.currentTextChanged.connect(update_animation)
        position_combo.currentTextChanged.connect(update_animation)
        curve_combo.currentTextChanged.connect(update_animation)
        
        # 初始化应用一次动画设置
        update_animation()
        
        return container

    def preview_animation(self, item: ImageItem):
        """预览动画效果"""
        try:
            # 获取当前行
            row = self.image_items.index(item) + 1
            
            # 状态栏显示处理中消息
            self.statusBar().showMessage("正在生成预览片段...")
            
            # 临时禁用UI
            self.disable_ui_during_processing(True)
            
            # 获取动画设置组件
            animation_widget = self.content_layout.itemAtPosition(row, 4).widget()
            
            # 获取控件
            scale_combo = animation_widget.findChild(QComboBox, "scale_combo")
            position_combo = animation_widget.findChild(QComboBox, "position_combo")
            curve_combo = animation_widget.findChild(QComboBox, "curve_combo")
            
            # 更新动画设置 - 组合缩放、平移和曲线
            scale_preset = scale_combo.currentText()
            position_preset = position_combo.currentText()
            curve_name = curve_combo.currentText()
            
            # 组合设置
            animation_settings = self.video_service.animation_service.combine_animation_settings(
                scale_preset, position_preset, curve_name
            )
            
            # 应用到item
            item.animation = animation_settings
            
            # 生成预览视频
            output_path = self.video_service.preview_clip(
                item.to_dict(),
                f"preview_{item.id}.mp4"
            )
            
            # 更新状态栏
            self.statusBar().showMessage(f"预览片段已生成：{output_path}")
            
            # 播放预览视频
            self.video_service.open_with_default_player(output_path)
            
        except Exception as e:
            # 仅在出错时显示对话框
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            # 恢复UI
            self.disable_ui_during_processing(False)

class VideoSettingsDialog(QDialog):
    """视频设置对话框"""
    
    def __init__(self, parent=None, video_service=None):
        super().__init__(parent)
        self.video_service = video_service
        self.setWindowTitle("视频设置")
        self.setMinimumWidth(400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 转场效果
        self.transition_combo = QComboBox()
        self.transition_combo.addItems(list(self.video_service.transitions.keys()))
        self.transition_combo.setCurrentText("随机")  # 默认选择随机转场
        form_layout.addRow("转场效果:", self.transition_combo)
        
        # 转场时长
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 3.0)
        self.duration_spin.setSingleStep(0.1)
        self.duration_spin.setValue(0.7)
        self.duration_spin.setSuffix(" 秒")
        form_layout.addRow("转场时长:", self.duration_spin)
        
        # 自定义转场选项
        self.custom_transitions_check = QCheckBox("为每个片段设置不同的转场效果")
        self.custom_transitions_check.setChecked(False)
        self.custom_transitions_check.stateChanged.connect(self.toggle_custom_transitions)
        form_layout.addRow("", self.custom_transitions_check)
        
        # 自定义转场列表
        self.custom_transitions_widget = QWidget()
        self.custom_transitions_layout = QVBoxLayout(self.custom_transitions_widget)
        self.custom_transitions_list = QListWidget()
        self.custom_transitions_layout.addWidget(QLabel("片段间转场:"))
        self.custom_transitions_layout.addWidget(self.custom_transitions_list)
        self.custom_transitions_widget.setVisible(False)
        form_layout.addRow("", self.custom_transitions_widget)
        
        # 视频分辨率选项
        self.resolution_check = QCheckBox("指定输出分辨率")
        self.resolution_check.setChecked(False)
        self.resolution_check.stateChanged.connect(self.toggle_resolution)
        form_layout.addRow("", self.resolution_check)
        
        # 分辨率设置
        self.resolution_widget = QWidget()
        resolution_layout = QHBoxLayout(self.resolution_widget)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 3840)
        self.width_spin.setSingleStep(10)
        self.width_spin.setValue(1920)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 2160)
        self.height_spin.setSingleStep(10)
        self.height_spin.setValue(1080)
        resolution_layout.addWidget(self.width_spin)
        resolution_layout.addWidget(QLabel("x"))
        resolution_layout.addWidget(self.height_spin)
        self.resolution_widget.setVisible(False)
        form_layout.addRow("分辨率:", self.resolution_widget)
        
        # 输出质量
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["低", "中", "高"])
        self.quality_combo.setCurrentText("中")
        form_layout.addRow("输出质量:", self.quality_combo)
        
        layout.addLayout(form_layout)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # 初始化自定义转场列表
        self.update_custom_transitions_list()
    
    def toggle_custom_transitions(self, state):
        """切换自定义转场选项的可见性"""
        self.custom_transitions_widget.setVisible(state != 0)
        if state != 0:
            self.update_custom_transitions_list()
    
    def toggle_resolution(self, state):
        """切换分辨率设置的可见性"""
        self.resolution_widget.setVisible(state != 0)
    
    def update_custom_transitions_list(self):
        """更新自定义转场列表"""
        # 获取父窗口的图片项目数量
        parent = self.parent()
        if hasattr(parent, 'image_items'):
            image_count = len(parent.image_items)
            transition_count = max(0, image_count - 1)
            
            self.custom_transitions_list.clear()
            
            transition_names = list(self.video_service.transitions.keys())
            default_transition = self.transition_combo.currentText()
            
            for i in range(transition_count):
                item = QListWidgetItem(f"片段 {i+1} 到 片段 {i+2}")
                self.custom_transitions_list.addItem(item)
                
                # 添加选择框
                combo = QComboBox()
                combo.addItems(transition_names)
                combo.setCurrentText(default_transition)
                
                self.custom_transitions_list.setItemWidget(item, combo)
    
    def get_settings(self) -> dict:
        """获取设置"""
        # 获取输出质量
        quality_map = {"低": "low", "中": "medium", "高": "high"}
        
        # 获取自定义转场列表
        custom_transitions = []
        if self.custom_transitions_check.isChecked():
            for i in range(self.custom_transitions_list.count()):
                item = self.custom_transitions_list.item(i)
                combo = self.custom_transitions_list.itemWidget(item)
                custom_transitions.append(combo.currentText())
        
        # 获取分辨率
        resolution = None
        if self.resolution_check.isChecked():
            resolution = (self.width_spin.value(), self.height_spin.value())
        
        return {
            "transition": self.transition_combo.currentText(),
            "transition_duration": self.duration_spin.value(),
            "use_custom_transitions": self.custom_transitions_check.isChecked(),
            "custom_transitions": custom_transitions,
            "video_resolution": resolution,
            "output_quality": quality_map[self.quality_combo.currentText()]
        } 