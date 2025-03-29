from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QScrollArea, QLabel, QTextEdit,
                             QFileDialog, QMessageBox, QProgressDialog,
                             QGridLayout, QFrame, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QGroupBox, QFormLayout, QComboBox,
                             QInputDialog, QSlider, QApplication)
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

class AnimationSettingsWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("动画设置", parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        # 随机动画按钮
        self.random_animation = QPushButton("随机动画")
        self.random_animation.clicked.connect(self.generate_random_animation)
        layout.addRow(self.random_animation)
        
        # 缩放设置
        self.scale_enabled = QCheckBox("启用缩放")
        self.scale_value = QDoubleSpinBox()
        self.scale_value.setRange(1.0, 3.0)
        self.scale_value.setValue(1.0)
        self.scale_value.setSingleStep(0.1)
        layout.addRow(self.scale_enabled, self.scale_value)
        
        # 位置设置
        self.position_enabled = QCheckBox("启用位置")
        self.position_enabled.setEnabled(False)  # 默认禁用
        self.position_enabled.stateChanged.connect(self.on_scale_changed)
        self.position_start_x = QSpinBox()
        self.position_start_x.setRange(-1000, 1000)
        self.position_start_y = QSpinBox()
        self.position_start_y.setRange(-1000, 1000)
        self.position_end_x = QSpinBox()
        self.position_end_x.setRange(-1000, 1000)
        self.position_end_y = QSpinBox()
        self.position_end_y.setRange(-1000, 1000)
        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel("X:"))
        position_layout.addWidget(self.position_start_x)
        position_layout.addWidget(QLabel("Y:"))
        position_layout.addWidget(self.position_start_y)
        position_layout.addWidget(QLabel("→"))
        position_layout.addWidget(QLabel("X:"))
        position_layout.addWidget(self.position_end_x)
        position_layout.addWidget(QLabel("Y:"))
        position_layout.addWidget(self.position_end_y)
        layout.addRow(self.position_enabled, position_layout)
        
        self.setLayout(layout)
    
    def on_scale_changed(self):
        """当缩放状态改变时，更新位置设置的启用状态"""
        self.position_enabled.setEnabled(self.scale_enabled.isChecked())
    
    def generate_random_animation(self):
        """生成随机动画设置"""
        import random
        
        # 随机启用/禁用各种动画
        self.scale_enabled.setChecked(random.choice([True, False]))
        self.position_enabled.setChecked(random.choice([True, False]))
        
        # 随机设置各种动画的值
        if self.scale_enabled.isChecked():
            self.scale_value.setValue(round(random.uniform(1.0, 2.0), 1))
        
        if self.position_enabled.isChecked():
            self.position_start_x.setValue(random.randint(-500, 500))
            self.position_start_y.setValue(random.randint(-500, 500))
            self.position_end_x.setValue(random.randint(-500, 500))
            self.position_end_y.setValue(random.randint(-500, 500))
    
    def get_animation_settings(self) -> Dict:
        """获取动画设置"""
        settings = {}
        
        if self.scale_enabled.isChecked():
            scale_value = self.scale_value.value()
            settings['scale'] = [1.0, scale_value]  # 从1.0开始缩放
        
        if self.position_enabled.isChecked():
            settings['position'] = [
                (self.position_start_x.value(), self.position_start_y.value()),
                (self.position_end_x.value(), self.position_end_y.value())
            ]
        
        return settings if settings else None

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
        """生成视频"""
        if not self.image_items:
            QMessageBox.warning(self, "警告", "请先添加图片")
            return
            
        # 检查是否所有图片都有语音
        items_without_audio = [item for item in self.image_items if not item.has_audio]
        if items_without_audio:
            QMessageBox.warning(self, "警告", "请先生成所有图片的语音")
            return
        
        # 更新所有项目的动画设置
        for row in range(1, self.content_layout.rowCount()):
            item = self.image_items[row - 1]
            animation_widget = self.content_layout.itemAtPosition(row, 4).widget()
            
            # 获取当前选择的预设动画和曲线
            preset_combo = animation_widget.findChild(QComboBox, "preset_combo")
            curve_combo = animation_widget.findChild(QComboBox, "curve_combo")
            
            preset_name = preset_combo.currentText()
            curve_name = curve_combo.currentText()
            
            if preset_name == "随机":
                item.animation = "随机"
            else:
                # 获取预设动画设置
                preset = self.video_service.animation_service.preset_animations[preset_name].copy()
                # 更新动画曲线
                preset['curve'] = curve_name
                item.animation = preset
        
        # 选择过渡效果
        transition, ok = QInputDialog.getItem(
            self,
            "选择过渡效果",
            "请选择视频片段之间的过渡效果：",
            list(self.video_service.transitions.keys()),
            0,
            False
        )
        
        if not ok:
            return
        
        # 创建输出目录
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 生成视频
        output_path = self.video_service.create_video(
            [item.to_dict() for item in self.image_items],
            str(output_dir / "final_video.mp4"),
            transition
        )
        
        if output_path:
            self.last_video_path = output_path
            self.preview_button.setEnabled(True)
            self.statusBar().showMessage(f"视频已生成：{output_path}")
    
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
            
            # 随机选择一个预设动画
            preset_combo = animation_widget.findChild(QComboBox, "preset_combo")
            preset_name = "随机"
            preset_combo.setCurrentText(preset_name)
            item.animation = preset_name
        
        # 获取当前动画设置
        if isinstance(item.animation, str):
            preset = item.animation
        else:
            preset = item.animation
        
        # 生成预览文件
        output_path = self.video_service.preview_clip(
            item.to_dict(),
            f"preview_{item.id}.mp4"
        )
        
        # 预览视频
        self.video_service.open_with_default_player(output_path)

    def create_animation_settings(self, item: ImageItem) -> QWidget:
        """创建动画设置部分"""
        animation_group = QGroupBox("动画设置")
        animation_layout = QVBoxLayout()
        
        # 预设动画选择
        preset_layout = QHBoxLayout()
        preset_label = QLabel("预设动画:")
        preset_combo = QComboBox()
        preset_combo.setObjectName("preset_combo")  # 设置对象名称
        preset_combo.addItems(self.video_service.animation_service.preset_animations.keys())
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(preset_combo)
        animation_layout.addLayout(preset_layout)
        
        # 动画曲线选择
        curve_layout = QHBoxLayout()
        curve_label = QLabel("动画曲线:")
        curve_combo = QComboBox()
        curve_combo.setObjectName("curve_combo")  # 设置对象名称
        curve_combo.addItems(self.video_service.animation_service.animation_curves.keys())
        curve_layout.addWidget(curve_label)
        curve_layout.addWidget(curve_combo)
        animation_layout.addLayout(curve_layout)
        
        # 预览按钮
        preview_button = QPushButton("预览动画")
        preview_button.clicked.connect(lambda: self.preview_animation(item))
        animation_layout.addWidget(preview_button)
        
        # 设置初始值
        if hasattr(item, 'animation') and item.animation:
            if isinstance(item.animation, str):
                preset_combo.setCurrentText(item.animation)
            elif isinstance(item.animation, dict):
                if 'curve' in item.animation:
                    curve_combo.setCurrentText(item.animation['curve'])
        
        # 连接信号
        preset_combo.currentTextChanged.connect(lambda text: self.update_animation_settings(item))
        curve_combo.currentTextChanged.connect(lambda text: self.update_animation_settings(item))
        
        animation_group.setLayout(animation_layout)
        return animation_group

    def update_animation_settings(self, item: ImageItem):
        """更新动画设置"""
        # 获取当前行的动画设置组件
        row = self.image_items.index(item) + 1
        animation_widget = self.content_layout.itemAtPosition(row, 4).widget()
        
        # 获取当前选择的预设动画和曲线
        preset_combo = animation_widget.findChild(QComboBox, "preset_combo")
        curve_combo = animation_widget.findChild(QComboBox, "curve_combo")
        
        preset_name = preset_combo.currentText()
        curve_name = curve_combo.currentText()
        
        if preset_name == "随机":
            item.animation = "随机"
        else:
            # 获取预设动画设置
            preset = self.video_service.animation_service.preset_animations[preset_name].copy()
            # 更新动画曲线
            preset['curve'] = curve_name
            item.animation = preset

    def preview_animation(self, item: ImageItem):
        """预览动画效果"""
        try:
            # 更新动画设置
            self.update_animation_settings(item)
            
            # 生成预览视频
            output_path = self.video_service.preview_clip(
                item.to_dict(),
                f"preview_{item.id}.mp4"
            )
            
            # 播放预览视频
            self.video_service.open_with_default_player(output_path)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览失败: {str(e)}") 