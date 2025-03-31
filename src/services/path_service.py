from pathlib import Path

class PathService:
    """路径服务，集中管理所有输出目录"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化所有路径"""
        self.output_dir = Path("output")
        self.video_dir = self.output_dir / "video"
        self.audio_dir = self.output_dir / "audio"
        
        # 创建所有必要的目录
        self.output_dir.mkdir(exist_ok=True)
        self.video_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)
    
    @property
    def audio_directory(self) -> Path:
        """获取音频目录路径"""
        return self.audio_dir
    
    @property
    def video_directory(self) -> Path:
        """获取视频目录路径"""
        return self.video_dir
    
    @property
    def output_directory(self) -> Path:
        """获取主输出目录路径"""
        return self.output_dir 