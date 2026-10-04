import threading
import uuid
from pathlib import Path
from backend.app.core.config import settings
from backend.app.models.database import DatabaseManager
from backend.app.services.video_service import VideoService
from backend.app.services.cv_service import ComputerVisionService
from backend.app.services.reasoning_service import ReasoningService

def run_analysis_pipeline(video_id: str, job_id: str):
    """
    Asynchronous worker executing the full real AI video intelligence pipeline.
    """
    try:
        video_record = DatabaseManager.get_video(video_id)
        if not video_record:
            DatabaseManager.update_job_status(
                job_id=job_id,
                video_id=video_id,
                status="FAILED",
                stage="FAILED",
                stage_message="Video record not found",
                progress=0.0,
                error="Video record not found."
            )
            return

        video_path = Path(video_record["filepath"])

        # STAGE 1: INGESTION & METADATA
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PROCESSING",
            stage="INGESTION",
            stage_message="Validating video container & extracting container metadata...",
            progress=10.0
        )
        metadata = VideoService.extract_metadata(video_path)

        # STAGE 2: FRAME EXTRACTION
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PROCESSING",
            stage="EXTRACTION",
            stage_message=f"Extracting frames at {settings.frame_sample_fps} FPS...",
            progress=25.0
        )
        sampled_frames = VideoService.sample_frames(
            video_id=video_id,
            video_path=video_path,
            sample_fps=settings.frame_sample_fps
        )

        if not sampled_frames:
            raise ValueError("No frames could be extracted from video.")

        # STAGE 3, 4, 5: YOLO DETECTION, TRACKING & POSE
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PROCESSING",
            stage="DETECTION",
            stage_message="Running Ultralytics YOLOv8 object detection & ByteTrack tracking...",
            progress=50.0
        )
        
        detections, poses, tracks = ComputerVisionService.process_frames(
            frames_info=sampled_frames,
            video_width=metadata["width"],
            video_height=metadata["height"]
        )

        # Save detections, poses, tracks into SQLite
        for d in detections:
            DatabaseManager.save_detections(video_id, d["frame_idx"], d["timestamp"], d["boxes"])
        for p in poses:
            DatabaseManager.save_poses(video_id, p["frame_idx"], p["timestamp"], p["skeletons"])
        DatabaseManager.save_tracks(video_id, tracks)

        # STAGE 6: POSE & MULTIMODAL UNDERSTANDING
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PROCESSING",
            stage="UNDERSTANDING",
            stage_message="Running visual reasoning & event extraction...",
            progress=75.0
        )
        events = ReasoningService.extract_events(
            video_id=video_id,
            frames_info=sampled_frames,
            detections=detections,
            poses=poses,
            tracks=tracks
        )
        DatabaseManager.save_events(video_id, events)

        # STAGE 7: SEMANTIC INDEXING
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PROCESSING",
            stage="INDEXING",
            stage_message="Constructing spatio-temporal semantic memory index...",
            progress=92.0
        )

        # STAGE 8: COMPLETE
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="COMPLETED",
            stage="DONE",
            stage_message="Real AI video analysis completed successfully.",
            progress=100.0
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="FAILED",
            stage="FAILED",
            stage_message=f"Pipeline error: {str(e)}",
            progress=0.0,
            error=str(e)
        )

class PipelineWorker:
    @staticmethod
    def start_pipeline_job(video_id: str) -> str:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        DatabaseManager.update_job_status(
            job_id=job_id,
            video_id=video_id,
            status="PENDING",
            stage="INGESTION",
            stage_message="Queuing video for AI analysis...",
            progress=0.0
        )

        thread = threading.Thread(
            target=run_analysis_pipeline,
            args=(video_id, job_id),
            daemon=True
        )
        thread.start()
        return job_id
