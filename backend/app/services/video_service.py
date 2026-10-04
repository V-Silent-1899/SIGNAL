import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
from backend.app.core.config import settings

class VideoService:
    ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}

    @staticmethod
    def validate_video_file(file_path: Path) -> Tuple[bool, str]:
        ext = file_path.suffix.lower()
        if ext not in VideoService.ALLOWED_EXTENSIONS:
            return False, f"Unsupported format '{ext}'. Supported formats: MP4, WebM, MOV."

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.max_video_size_mb:
            return False, f"File size ({file_size_mb:.1f} MB) exceeds maximum limit of {settings.max_video_size_mb} MB."

        # Test opening with OpenCV
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            return False, "Failed to decode video file. The file may be corrupt or unreadable."

        cap.release()
        return True, "Valid video file."

    @staticmethod
    def extract_metadata(file_path: Path) -> Dict[str, Any]:
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            raise ValueError("Could not open video file.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        duration = total_frames / fps if fps > 0 else 0.0

        cap.release()

        file_size = file_path.stat().st_size

        return {
            "duration": round(duration, 2),
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "codec": "h264",
            "file_size": file_size
        }

    @staticmethod
    def sample_frames(video_id: str, video_path: Path, sample_fps: float = 1.0) -> List[Dict[str, Any]]:
        """
        Samples frames at sample_fps (default 1 frame per second)
        Saves each frame to data/frames/{video_id}/frame_{frame_idx:06d}.jpg
        Returns list of { "frame_idx": int, "timestamp": float, "path": str, "relative_url": str }
        """
        frames_dir = settings.frames_dir / video_id
        frames_dir.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("Could not open video for frame extraction.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_interval = max(1, int(round(fps / sample_fps)))

        sampled_frames: List[Dict[str, Any]] = []
        current_frame = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if current_frame % frame_interval == 0:
                timestamp = round(current_frame / fps, 2)
                frame_filename = f"frame_{current_frame:06d}.jpg"
                frame_out_path = frames_dir / frame_filename

                # Resize if frame is excessively large
                h, w = frame.shape[:2]
                if w > settings.analysis_frame_width:
                    scale = settings.analysis_frame_width / float(w)
                    new_w = settings.analysis_frame_width
                    new_h = int(h * scale)
                    frame_to_save = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                else:
                    frame_to_save = frame

                cv2.imwrite(str(frame_out_path), frame_to_save, [cv2.IMWRITE_JPEG_QUALITY, 85])

                sampled_frames.append({
                    "frame_idx": current_frame,
                    "timestamp": timestamp,
                    "path": str(frame_out_path),
                    "filename": frame_filename,
                    "relative_url": f"/api/videos/{video_id}/frames/{frame_filename}"
                })

            current_frame += 1

        cap.release()
        return sampled_frames
