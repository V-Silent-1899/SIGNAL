import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Root of the workspace
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(WORKSPACE_ROOT / ".env")

class SystemSettings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "SIGNAL")
    app_env: str = os.getenv("APP_ENV", "development")
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Qwen Multimodal Reasoning
    qwen_model_id: str = os.getenv("QWEN_MODEL_ID", "Qwen/Qwen2.5-VL-7B-Instruct")
    qwen_device: str = os.getenv("QWEN_DEVICE", "auto")
    qwen_dtype: str = os.getenv("QWEN_DTYPE", "auto")
    qwen_api_base_url: Optional[str] = os.getenv("QWEN_API_BASE_URL") or None
    qwen_api_key: Optional[str] = os.getenv("QWEN_API_KEY") or None

    # YOLO Models
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    yolo_pose_model_path: str = os.getenv("YOLO_POSE_MODEL_PATH", "yolov8n-pose.pt")
    yolo_confidence_threshold: float = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.35"))
    yolo_tracker: str = os.getenv("YOLO_TRACKER", "bytetrack.yaml")

    # Semantic Retrieval (BGE-M3 or fallback)
    bge_model_id: str = os.getenv("BGE_MODEL_ID", "BAAI/bge-m3")
    enable_semantic_search: bool = os.getenv("ENABLE_SEMANTIC_SEARCH", "true").lower() == "true"

    # Video Pipeline constraints
    max_video_size_mb: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
    max_video_duration_seconds: int = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "300"))
    frame_sample_fps: float = float(os.getenv("FRAME_SAMPLE_FPS", "1.0"))
    analysis_frame_width: int = int(os.getenv("ANALYSIS_FRAME_WIDTH", "1280"))

    # FFmpeg executable path
    ffmpeg_path: str = os.getenv(
        "FFMPEG_PATH",
        r"C:\Users\91810\.antigravity-ide\extensions\kilocode.kilo-code-7.8.3-win32-x64\bin\ffmpeg.exe"
    )

    # Directories
    workspace_root: Path = WORKSPACE_ROOT
    upload_dir: Path = WORKSPACE_ROOT / os.getenv("UPLOAD_DIR", "./data/uploads")
    results_dir: Path = WORKSPACE_ROOT / os.getenv("RESULTS_DIR", "./data/results")
    frames_dir: Path = WORKSPACE_ROOT / os.getenv("FRAMES_DIR", "./data/frames")
    models_dir: Path = WORKSPACE_ROOT / "models"
    db_path: Path = WORKSPACE_ROOT / os.getenv("DB_PATH", "./data/signal.sqlite3")

    max_workers: int = int(os.getenv("MAX_WORKERS", "2"))

settings = SystemSettings()

# Ensure directories exist
for directory in [settings.upload_dir, settings.results_dir, settings.frames_dir, settings.models_dir, settings.db_path.parent]:
    directory.mkdir(parents=True, exist_ok=True)
