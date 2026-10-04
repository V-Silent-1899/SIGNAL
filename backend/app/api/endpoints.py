import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.models.database import DatabaseManager
from backend.app.schemas.video import VideoResponse, UploadResponse, VideoMetadata
from backend.app.schemas.system import SystemStatusResponse
from backend.app.schemas.analysis import AnalysisStatusResponse
from backend.app.schemas.event import EventsResponse, EventItem
from backend.app.schemas.detection import DetectionsResponse, TracksResponse, FrameDetections, TrackItem
from backend.app.schemas.qa import QuestionRequest, QuestionResponse, EvidenceItem
from backend.app.services.system_service import SystemService
from backend.app.services.video_service import VideoService
from backend.app.services.qa_service import VideoQAService
from backend.app.services.demo_service import DemoService, DEMO_VIDEO_ID
from backend.app.workers.pipeline_worker import PipelineWorker

router = APIRouter()

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env
    }

@router.get("/system/status", response_model=SystemStatusResponse)
def get_system_status():
    return SystemService.get_system_status()

@router.get("/videos", response_model=List[VideoResponse])
def list_videos():
    videos = DatabaseManager.list_videos()
    out = []
    for v in videos:
        out.append(VideoResponse(
            id=v["id"],
            filename=v["filename"],
            file_size=v["file_size"],
            duration=v["duration"],
            status=v["status"],
            created_at=v["created_at"],
            metadata=VideoMetadata(
                duration=v["duration"] or 0.0,
                fps=v["fps"] or 25.0,
                total_frames=v["total_frames"] or 0,
                width=v["width"] or 1280,
                height=v["height"] or 720,
                codec="h264",
                file_size=v["file_size"]
            )
        ))
    return out

@router.post("/videos/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    filename = file.filename or "video.mp4"
    video_id = f"vid_{uuid.uuid4().hex[:10]}"
    ext = Path(filename).suffix.lower()

    if ext not in VideoService.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported formats: MP4, WebM, MOV."
        )

    dest_filename = f"{video_id}_{filename}"
    dest_path = settings.upload_dir / dest_filename

    # Stream write upload
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate video
    is_valid, err_msg = VideoService.validate_video_file(dest_path)
    if not is_valid:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=err_msg)

    # Extract metadata
    try:
        metadata_dict = VideoService.extract_metadata(dest_path)
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to read video metadata: {str(e)}")

    file_size = dest_path.stat().st_size
    DatabaseManager.insert_video(
        video_id=video_id,
        filename=filename,
        filepath=str(dest_path),
        file_size=file_size,
        metadata=metadata_dict,
        is_demo=False
    )

    metadata = VideoMetadata(**metadata_dict)
    return UploadResponse(
        video_id=video_id,
        filename=filename,
        message="Video uploaded and validated successfully.",
        metadata=metadata
    )

@router.get("/videos/{video_id}", response_model=VideoResponse)
def get_video_info(video_id: str):
    v = DatabaseManager.get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found.")

    return VideoResponse(
        id=v["id"],
        filename=v["filename"],
        file_size=v["file_size"],
        duration=v["duration"],
        status=v["status"],
        created_at=v["created_at"],
        metadata=VideoMetadata(
            duration=v["duration"] or 0.0,
            fps=v["fps"] or 25.0,
            total_frames=v["total_frames"] or 0,
            width=v["width"] or 1280,
            height=v["height"] or 720,
            codec="h264",
            file_size=v["file_size"]
        )
    )

@router.get("/videos/{video_id}/stream")
def stream_video(video_id: str):
    v = DatabaseManager.get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found.")

    filepath = Path(v["filepath"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video file missing on disk.")

    media_type = "video/mp4"
    if filepath.suffix.lower() == ".webm":
        media_type = "video/webm"
    elif filepath.suffix.lower() == ".mov":
        media_type = "video/quicktime"

    return FileResponse(path=str(filepath), media_type=media_type)

@router.get("/videos/{video_id}/frames/{frame_filename}")
def get_frame_image(video_id: str, frame_filename: str):
    frames_dir = settings.frames_dir / video_id
    frame_path = frames_dir / frame_filename
    if frame_path.exists():
        return FileResponse(path=str(frame_path), media_type="image/jpeg")

    # If exact frame doesn't exist, find closest existing frame
    if frames_dir.exists():
        existing_frames = sorted(list(frames_dir.glob("*.jpg")))
        if existing_frames:
            # Extract numbers if possible to find nearest frame
            import re
            req_nums = re.findall(r"\d+", frame_filename)
            if req_nums:
                target_num = int(req_nums[0])
                best_file = existing_frames[0]
                best_diff = float("inf")
                for ef in existing_frames:
                    ef_nums = re.findall(r"\d+", ef.name)
                    if ef_nums:
                        diff = abs(int(ef_nums[0]) - target_num)
                        if diff < best_diff:
                            best_diff = diff
                            best_file = ef
                return FileResponse(path=str(best_file), media_type="image/jpeg")
            return FileResponse(path=str(existing_frames[0]), media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="Frame not found.")

@router.post("/videos/{video_id}/analyze")
def start_analysis(video_id: str):
    v = DatabaseManager.get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found.")

    # Check if already completed
    existing_job = DatabaseManager.get_job_by_video(video_id)
    if existing_job and existing_job["status"] == "COMPLETED":
        return {
            "video_id": video_id,
            "job_id": existing_job["id"],
            "status": "COMPLETED",
            "message": "Analysis results already cached."
        }

    job_id = PipelineWorker.start_pipeline_job(video_id)
    return {
        "video_id": video_id,
        "job_id": job_id,
        "status": "PROCESSING",
        "message": "Real AI video intelligence analysis started."
    }

@router.get("/videos/{video_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(video_id: str):
    job = DatabaseManager.get_job_by_video(video_id)
    if not job:
        # Check if video exists
        v = DatabaseManager.get_video(video_id)
        if not v:
            raise HTTPException(status_code=404, detail="Video not found.")
        return AnalysisStatusResponse(
            video_id=video_id,
            job_id="",
            status="IDLE",
            stage="INGESTION",
            progress=0.0,
            stage_message="Ready for analysis.",
            is_demo=bool(v.get("is_demo", 0))
        )

    return AnalysisStatusResponse(
        video_id=video_id,
        job_id=job["id"],
        status=job["status"],
        stage=job["stage"],
        progress=job["progress"],
        stage_message=job["stage_message"] or "",
        error=job["error"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        is_demo=bool(job.get("is_demo", 0))
    )

@router.get("/videos/{video_id}/events", response_model=EventsResponse)
def get_events(video_id: str):
    events_raw = DatabaseManager.get_events(video_id)
    events: List[EventItem] = []
    for er in events_raw:
        events.append(EventItem(
            id=er["id"],
            video_id=video_id,
            timestamp_start=er["timestamp_start"],
            timestamp_end=er["timestamp_end"],
            title=er["title"],
            description=er["description"],
            importance=er.get("importance", "medium"),
            confidence=er["confidence"],
            subjects=er.get("subjects", []),
            objects=er.get("objects", []),
            evidence_frames=er.get("evidence_frames", []),
            evidence_urls=[f"/api/videos/{video_id}/frames/frame_{int(f):06d}.jpg" for f in er.get("evidence_frames", [])],
            created_at=er.get("created_at")
        ))
    return EventsResponse(video_id=video_id, total_events=len(events), events=events)

@router.get("/videos/{video_id}/tracks", response_model=TracksResponse)
def get_tracks(video_id: str):
    tracks_raw = DatabaseManager.get_tracks(video_id)
    tracks: List[TrackItem] = [TrackItem(**t) for t in tracks_raw]
    return TracksResponse(video_id=video_id, total_tracks=len(tracks), tracks=tracks)

@router.get("/videos/{video_id}/detections", response_model=DetectionsResponse)
def get_detections(video_id: str):
    dets_raw = DatabaseManager.get_detections(video_id)
    poses_raw = DatabaseManager.get_poses(video_id)
    poses_by_frame = {p["frame_idx"]: p["skeletons"] for p in poses_raw}

    frames: List[FrameDetections] = []
    for d in dets_raw:
        f_idx = d["frame_idx"]
        skeletons = poses_by_frame.get(f_idx, [])
        frames.append(FrameDetections(
            frame_idx=f_idx,
            timestamp=d["timestamp"],
            boxes=d["boxes"],
            skeletons=skeletons
        ))

    return DetectionsResponse(video_id=video_id, total_frames=len(frames), frames=frames)

@router.get("/videos/{video_id}/poses")
def get_poses(video_id: str):
    return DatabaseManager.get_poses(video_id)

@router.post("/videos/{video_id}/ask", response_model=QuestionResponse)
def ask_video(video_id: str, req: QuestionRequest):
    v = DatabaseManager.get_video(video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found.")

    return VideoQAService.answer_question(video_id, req.question)

@router.get("/videos/{video_id}/evidence/{timestamp}")
def get_evidence_at_timestamp(video_id: str, timestamp: float):
    # Find closest frame
    frames_dir = settings.frames_dir / video_id
    if not frames_dir.exists():
        raise HTTPException(status_code=404, detail="No frames available.")

    frame_idx = int(round(timestamp))
    frame_filename = f"frame_{frame_idx:06d}.jpg"
    frame_path = frames_dir / frame_filename

    if not frame_path.exists():
        # pick closest existing
        existing_frames = sorted(list(frames_dir.glob("*.jpg")))
        if not existing_frames:
            raise HTTPException(status_code=404, detail="No frame found.")
        frame_path = existing_frames[0]
        frame_filename = frame_path.name

    return {
        "video_id": video_id,
        "timestamp": timestamp,
        "frame_idx": frame_idx,
        "image_url": f"/api/videos/{video_id}/frames/{frame_filename}"
    }

@router.post("/demo/load")
def load_precomputed_demo():
    demo_id = DemoService.ensure_demo_dataset()
    return {
        "status": "success",
        "video_id": demo_id,
        "mode": "PRECOMPUTED DEMO ANALYSIS",
        "message": "Demo surveillance laboratory dataset loaded with precomputed events & tracks."
    }
