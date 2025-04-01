# Image2Video API服务

本目录包含了将Image2Video功能封装为HTTP API的服务器代码，专为Coze插件开发设计。

## 目录结构

```
api/
├── api_server.py        # API服务器主文件
├── api_uploads/         # 上传的图片和音频文件存储目录
├── api_output/          # 生成的视频文件存储目录
├── api_temp/            # 临时文件存储目录
├── logs/                # 日志文件目录
├── start.sh             # 启动脚本
├── cleanup.sh           # 清理临时文件脚本
├── test_api.py          # API测试脚本
├── deploy.sh            # 自动部署脚本
├── Dockerfile           # Docker镜像构建文件
├── docker-compose.yml   # Docker Compose配置文件
├── SERVER_DEPLOY.md     # 服务器部署说明
├── coze_plugin.md       # Coze插件配置说明
└── README.md            # 本说明文件
```

## 快速启动

### 方法一：直接运行

1. 确保已安装项目依赖：
   ```bash
   pip install -r ../requirements.txt
   ```

2. 运行启动脚本：
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. API服务将在 http://localhost:8000 启动

### 方法二：使用Docker Compose

1. 确保已安装Docker和Docker Compose

2. 在api目录下运行：
   ```bash
   docker-compose up -d
   ```

3. API服务将在 http://localhost:5000 启动

## API接口详细说明

### 1. 图片转视频API

#### 接口地址
```
POST /api/image2video
```

#### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|-------|------|------|-----|
| image_url | string | 是(与image_base64二选一) | 图片的URL地址 |
| image_base64 | string | 是(与image_url二选一) | Base64编码的图片数据 |
| audio_url | string | 否 | 音频URL，将作为视频的背景音乐 |
| animation_type | string | 否 | 动画类型，默认为"放大" |
| animation_curve | string | 否 | 动画曲线，默认为"线性" |
| duration | number | 否 | 视频时长(秒)，默认为5秒 |
| output_quality | string | 否 | 输出质量，可选值: "low", "medium", "high"，默认为"medium" |

#### 动画类型选项：
- **无**: 保持原始大小
- **放大**: 从原始尺寸向外放大
- **缩小**: 从放大状态缩小到原始尺寸
- **轻微放大**: 轻微的放大效果
- **轻微缩小**: 轻微的缩小效果
- **剧烈放大**: 更强的放大效果
- **脉动**: 轻微的呼吸式缩放效果
- **左到右**: 画面从左向右移动
- **右到左**: 画面从右向左移动
- **上到下**: 画面从上向下移动
- **下到上**: 画面从下向上移动
- 以及其他组合动画类型

#### 动画曲线选项：
- **线性**: 匀速变化
- **缓入**: 从慢到快
- **缓出**: 从快到慢
- **缓入缓出**: 先慢后快再慢
- **强缓入**: 更强烈的缓入效果
- **强缓出**: 更明显的缓出效果
- **平滑弹入**: 平滑带有弹性的进入效果
- **平滑弹出**: 平滑带有弹性的退出效果

#### 请求示例

```json
{
  "image_url": "https://example.com/image.jpg",
  "audio_url": "https://example.com/audio.mp3",
  "animation_type": "放大",
  "animation_curve": "缓入缓出",
  "duration": 10,
  "output_quality": "high"
}
```

#### 响应参数

| 参数名 | 类型 | 描述 |
|-------|------|-----|
| status | string | 处理状态，"success"或"error" |
| video_url | string | 生成的视频URL，仅当status为"success"时存在 |
| error | string | 错误信息，仅当status为"error"时存在 |

#### 响应示例

```json
{
  "status": "success",
  "video_url": "https://your-api-server.com/api/videos/abcdef-123456.mp4"
}
```

### 2. 视频合成API

#### 接口地址
```
POST /api/merge-videos
```

#### 请求参数

| 参数名 | 类型 | 必需 | 描述 |
|-------|------|------|-----|
| video_urls | array | 是 | 视频URL数组 |
| transition_type | string | 否 | 转场类型，默认为"淡入淡出" |
| transition_duration | number | 否 | 转场时长(秒)，默认为0.7秒 |
| output_quality | string | 否 | 输出质量，可选值: "low", "medium", "high"，默认为"medium" |
| output_resolution | string | 否 | 输出分辨率，格式为"宽x高"，如: "1280x720" |

#### 转场类型选项：
- **无**: 无转场效果
- **淡入淡出**: 两个场景之间的交叉溶解
- **滑动-左**: 新场景从左侧滑入
- **滑动-右**: 新场景从右侧滑入
- **滑动-上**: 新场景从顶部滑入
- **滑动-下**: 新场景从底部滑入
- **缩放淡入**: 新场景逐渐放大进入
- **旋转淡入**: 新场景旋转进入
- **百叶窗**: 像百叶窗一样逐渐显示新场景
- **扭曲溶解**: 带有波浪扭曲效果的溶解
- **闪白过渡**: 通过闪白效果过渡到新场景

#### 请求示例

```json
{
  "video_urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/video3.mp4"
  ],
  "transition_type": "淡入淡出",
  "transition_duration": 1.0,
  "output_quality": "high",
  "output_resolution": "1920x1080"
}
```

#### 响应参数

| 参数名 | 类型 | 描述 |
|-------|------|-----|
| status | string | 处理状态，"success"或"error" |
| video_url | string | 生成的视频URL，仅当status为"success"时存在 |
| error | string | 错误信息，仅当status为"error"时存在 |

#### 响应示例

```json
{
  "status": "success",
  "video_url": "https://your-api-server.com/api/videos/uvwxyz-789012.mp4"
}
```

### 3. 视频下载
- **路径**: `/api/videos/<filename>`
- **方法**: `GET`
- **功能**: 下载生成的视频文件

### 4. 健康检查
- **路径**: `/health`
- **方法**: `GET`
- **功能**: 检查API服务是否正常运行

## 错误处理

### 常见错误代码

| HTTP状态码 | 错误描述 |
|-----------|---------|
| 400 | 请求参数错误，如缺少必需参数或参数格式不正确 |
| 404 | 资源不存在，如请求的视频文件不存在 |
| 500 | 服务器内部错误，处理请求时发生异常 |

### 错误响应示例

```json
{
  "status": "error",
  "error": "缺少图片参数(image_url或image_base64)"
}
```

## 维护

### 清理临时文件
运行清理脚本删除超过3天的临时文件：
```bash
./cleanup.sh
```

### 查看日志
```bash
tail -f logs/api.log
```

## 其他说明文件

- `SERVER_DEPLOY.md`: 详细的服务器部署指南，包括手动和一键部署方式
- `coze_plugin.md`: Coze插件配置说明，包括如何在Coze平台上创建插件 