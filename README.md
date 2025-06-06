# Image2Video

基于OpenCV和MoviePy的图片转视频工具，支持高质量动画效果和平滑过渡。

## 项目特点

- **高精度动画效果**：使用OpenCV实现的高精度动画效果，完全消除抖动和黑边问题
- **平滑转场**：多种精心设计的转场效果，支持自然平滑的片段衔接
- **多段视频合成**：支持多个视频片段合成，自动处理片段间的转场效果
- **丰富的动画预设**：内置20多种专业级摄像机效果（推、拉、移动、缩放+平移组合等）
- **灵活的动画曲线**：支持10种动画曲线（线性、缓入缓出、弹性、跳跃等）及随机选项
- **直观的用户界面**：基于PyQt6的简洁界面，易于操作
- **智能文件命名**：使用图片名称作为音频和视频片段文件名，方便管理和关联
- **自动音频生成**：合成视频时自动检测并生成缺失的音频文件
- **时间戳文件命名**：使用日期时间+流水号对输出视频进行命名，避免文件覆盖
- **模块化架构**：清晰的MVC架构设计，业务逻辑与UI完全分离，便于维护和扩展
- **片段重用机制**：自动检测和重用已生成的视频片段，避免重复处理，提高效率
- **集中路径管理**：使用统一的路径服务管理所有存储位置，简化目录结构

## 安装步骤

1. 确保已安装Python 3.7+
2. 克隆仓库
   ```
   git clone https://github.com/hugochou/image2video.git
   cd image2video
   ```
3. 创建并激活虚拟环境
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```
4. 安装依赖
   ```
   pip install -r requirements.txt
   ```

## 使用方法

1. 运行程序
   ```
   python run.py
   ```
2. 使用界面添加图片
3. 选择动画预设和曲线
4. 点击"生成片段"预览单个图片效果（如已生成则直接使用现有片段）
5. 完成所有图片设置后，点击"生成视频"创建完整视频

## 动画类型

### 缩放效果
- **无**：保持原始大小
- **放大**：从原始尺寸向外放大(1.0→1.2)
- **缩小**：从放大状态缩小到原始尺寸(1.2→1.0)
- **轻微放大**：轻微的放大效果(1.0→1.1)
- **轻微缩小**：轻微的缩小效果(1.1→1.0)
- **剧烈放大**：更强的放大效果(1.0→1.25)
- **脉动**：轻微的呼吸式缩放效果(1.0→1.05)
- **随机**：随机选择以上效果之一

### 平移效果
- **无**：保持位置不变
- **左到右**：画面从左向右移动
- **右到左**：画面从右向左移动
- **上到下**：画面从上向下移动
- **下到上**：画面从下向上移动
- **左上到右下**：画面从左上方向右下方移动
- **右上到左下**：画面从右上方向左下方移动
- **左下到右上**：画面从左下方向右上方移动
- **右下到左上**：画面从右下方向左上方移动
- **轻微左右**：较为微妙的左右移动
- **轻微上下**：较为微妙的上下移动
- **随机**：随机选择以上效果之一

### 预设组合
- **静止**：无任何动画效果
- **缩放-放大**：画面逐渐放大
- **缩放-缩小**：画面逐渐缩小
- **平移-各方向**：画面从一侧移动到另一侧
- **缩放+平移**：同时进行缩放和平移，有多种组合方向
- **跳动**：带有轻微弹跳效果的动画

## 动画曲线

- **线性**：匀速变化
- **缓入**：从慢到快
- **缓出**：从快到慢
- **缓入缓出**：先慢后快再慢
- **强缓入**：更强烈的缓入效果
- **强缓出**：更明显的缓出效果
- **平滑弹入**：平滑带有弹性的进入效果
- **平滑弹出**：平滑带有弹性的退出效果
- **随机**：随机选择以上任一曲线

## 转场效果

### 基本转场
- **无**：无转场效果，直接切换到下一个片段
- **淡入淡出**：两个场景之间的平滑交叉溶解
- **滑动**：多方向滑动转场
  - **滑动-左**：新场景从左侧滑入
  - **滑动-右**：新场景从右侧滑入
  - **滑动-上**：新场景从顶部滑入
  - **滑动-下**：新场景从底部滑入

### 高级转场
- **缩放淡入**：新场景逐渐放大进入
- **旋转淡入**：新场景旋转进入
- **百叶窗**：像百叶窗一样逐渐显示新场景
- **扭曲溶解**：带有波浪扭曲效果的溶解
- **闪白过渡**：通过闪白效果过渡到新场景
- **随机**：随机选择一种转场效果

### 自定义转场
- **转场序列**：为每个片段连接点单独设置转场效果
- **混合转场**：支持混合使用多种转场效果

## 视频合成选项

- **自定义转场序列**：为每个片段交接处单独设置转场效果
- **转场时长调整**：自定义转场效果的持续时间（默认0.7秒）
- **输出分辨率**：支持自定义输出视频的分辨率
- **输出质量**：支持低、中、高三种质量预设

## 技术实现

### 动画引擎
项目使用OpenCV实现高精度图像变换，通过以下技术确保动画效果的平滑和精确：

1. **仿射变换矩阵**：使用精确的变换矩阵控制图像的缩放和平移
2. **智能边缘处理**：根据平移量自动增加缩放，避免黑边
3. **精确曲线控制**：使用数学曲线函数精确控制动画进度
4. **高质量图像处理**：使用立方插值确保平滑变换
5. **过采样抗抖动**：3倍过采样率减少动画抖动

### 转场系统
转场效果基于OpenCV的高级帧处理，使用各种视觉技术创建平滑过渡：

1. **交叉淡入淡出**：使用加权混合实现平滑过渡
2. **滑动转场**：使用仿射变换实现方向滑动
3. **旋转过渡**：结合旋转变换和透明度混合
4. **特效转场**：百叶窗、扭曲溶解、闪白等高级视觉效果
5. **自定义转场序列**：支持为每个连接点单独设置不同的转场效果

### 文件管理
项目实现了智能的文件命名和管理机制：

1. **集中路径管理**：使用单例模式的PathService统一管理所有路径
2. **智能文件命名**：使用图片名称作为视频片段文件名
3. **时间戳命名**：使用日期时间+随机ID命名最终视频
4. **片段重用机制**：缓存和检测已生成的片段
5. **动画设置变更追踪**：当动画设置更改时自动清除缓存

### 音频处理
项目实现了完整的音频生成和处理流程：

1. **文本转语音**：使用gTTS将文本转换为自然语音
2. **自动音频生成**：检测并生成缺失的音频
3. **音视频同步**：确保音频和视频长度匹配
4. **图片关联命名**：使用图片名称作为音频文件名

## 项目架构

项目采用标准MVC模式设计，清晰分离业务逻辑和用户界面：

### 目录结构
```
image2video/
├── src/                  # 源代码目录
│   ├── models/          # 数据模型
│   ├── views/           # 视图层
│   ├── controllers/     # 控制器层
│   └── services/        # 服务层
├── output/              # 输出目录
│   ├── audio/          # 音频文件目录
│   └── video/          # 视频文件目录
├── tests/              # 测试目录
├── requirements.txt    # 项目依赖
└── README.md          # 项目文档
```

### 组件说明
1. **Model层**：
   - **ImageItem**：表示包含图片、音频和动画设置的项目

2. **View层**：
   - **MainWindow**：主用户界面，处理用户交互和显示
   - **VideoSettingsDialog**：视频设置对话框

3. **Controller层**：
   - **AudioController**：处理音频生成和预览相关的业务逻辑
   - **VideoController**：处理视频生成和合成相关的业务逻辑，负责片段重用逻辑

4. **Service层**：
   - **PathService**：集中管理所有输出路径，使用单例模式确保全局一致性
   - **VideoService**：负责视频创建、片段生成和最终合成
   - **AnimationService**：专门处理动画效果，包含预设和曲线实现
   - **TransitionService**：处理转场效果，提供多种转场选择
   - **AudioService**：负责音频处理和语音生成

## 系统要求
- Python 3.7 或更高版本
- 操作系统：Windows/macOS/Linux
- OpenCV-Python (用于高精度图像处理)
- MoviePy (用于视频合成)
- PyQt6 (用于用户界面)
- gTTS (用于文本转语音)

## 当前状态

### 已完成
- [x] 高精度OpenCV动画系统
- [x] 多种动画预设和曲线
- [x] 高质量转场效果
- [x] 音频与视频同步
- [x] 用户界面
- [x] 完整的视频导出流程
- [x] 多段视频合成
- [x] 自定义转场序列
- [x] 自定义输出质量和分辨率
- [x] 智能文件命名系统
- [x] 自动音频生成
- [x] MVC架构重构
- [x] 时间戳视频命名
- [x] 片段重用机制
- [x] 集中路径管理服务

### 计划中
- [ ] 更多的动画预设
- [ ] 支持3D转场效果
- [ ] 批量处理功能
- [ ] 增加文本标题和字幕支持
- [ ] 支持视频片段输入

## 使用示例

1. 创建简单的图片幻灯片：
   - 添加多张图片
   - 选择"缩放-放大"动画和"缓入缓出"曲线
   - 使用"淡入淡出"转场
   - 生成平滑过渡的视频

2. 创建专业视频展示：
   - 添加高分辨率图片
   - 为每张图片选择不同的动画效果和曲线
   - 为每个转场点选择不同的转场效果
   - 添加配音文本
   - 导出高质量视频

## 贡献
欢迎提交Pull Request或Issue。

## 许可
本项目遵循MIT许可证。 