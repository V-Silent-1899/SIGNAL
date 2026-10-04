import math
import uuid
import numpy as np
import cv2
from pathlib import Path
from backend.app.core.config import settings
from backend.app.models.database import DatabaseManager, init_db

DEMO_VIDEO_ID = "demo_surveillance_01"

COCO_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]

class DemoService:
    @staticmethod
    def ensure_demo_dataset():
        """
        Creates a legitimate, precomputed demonstration video and analysis dataset
        with strict labeling: PRECOMPUTED DEMO ANALYSIS.
        """
        init_db()
        existing = DatabaseManager.get_video(DEMO_VIDEO_ID)
        if existing:
            return DEMO_VIDEO_ID

        demo_video_path = settings.upload_dir / "demo_controlled_lab.mp4"
        frames_dir = settings.frames_dir / DEMO_VIDEO_ID
        frames_dir.mkdir(parents=True, exist_ok=True)

        width = 1280
        height = 720
        fps = 25
        duration_seconds = 65
        total_frames = fps * duration_seconds

        # Synthesize a clean, professional lab/workstation surveillance demonstration video
        # if demo video does not exist yet on disk
        if not demo_video_path.exists():
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(demo_video_path), fourcc, fps, (width, height))

            for frame_num in range(0, total_frames, 5): # write every 5th to keep creation fast
                # High-contrast, clean interior workspace background
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                frame[:] = (18, 20, 26) # dark slate background

                # Floor grid perspective
                cv2.line(frame, (100, 700), (400, 300), (32, 36, 48), 2)
                cv2.line(frame, (1180, 700), (880, 300), (32, 36, 48), 2)
                cv2.line(frame, (400, 300), (880, 300), (32, 36, 48), 2)

                # Monitored Table / Pedestal
                table_x1, table_y1, table_x2, table_y2 = 540, 360, 740, 480
                cv2.rectangle(frame, (table_x1, table_y1), (table_x2, table_y2), (45, 52, 68), -1)
                cv2.rectangle(frame, (table_x1, table_y1), (table_x2, table_y2), (70, 80, 105), 2)

                t = frame_num / fps

                # Object: Red Box on table until picked up at t=37s
                if t < 37.0:
                    box_x, box_y = 620, 335
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 50, box_y + 35), (35, 45, 215), -1)
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 50, box_y + 35), (80, 100, 255), 2)
                elif t < 58.0:
                    # Carried by person
                    p_pos_x = 200 + min(420, (t - 5.0) * 20) if t < 37.0 else 620 + (t - 37.0) * 18
                    box_x = int(p_pos_x + 25)
                    box_y = int(320 + math.sin(t * 4) * 8)
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 50, box_y + 35), (35, 45, 215), -1)
                    cv2.rectangle(frame, (box_x, box_y), (box_x + 50, box_y + 35), (80, 100, 255), 2)

                # Person appears at t >= 5s, walks to table by 35s, stays, walks away at 42s, exits at 58s
                if 5.0 <= t <= 58.0:
                    if t < 35.0:
                        px = int(150 + ((t - 5.0) / 30.0) * 450) # walks to 600
                    elif t <= 42.0:
                        px = 600 # interacts at table
                    else:
                        px = int(600 + ((t - 42.0) / 16.0) * 600) # walks to 1200
                    
                    py = 280
                    # Draw subtle person silhouette
                    cv2.circle(frame, (px + 30, py + 25), 20, (180, 190, 205), -1) # head
                    cv2.line(frame, (px + 30, py + 45), (px + 30, py + 140), (160, 175, 195), 10) # torso
                    cv2.line(frame, (px + 30, py + 70), (px + 10, py + 120), (160, 175, 195), 6) # left arm
                    cv2.line(frame, (px + 30, py + 70), (px + 50, py + 115), (160, 175, 195), 6) # right arm
                    cv2.line(frame, (px + 30, py + 140), (px + 15, py + 230), (140, 155, 175), 8) # left leg
                    cv2.line(frame, (px + 30, py + 140), (px + 45, py + 230), (140, 155, 175), 8) # right leg

                # Workstation HUD timestamp watermark
                time_code = f"SIGNAL LIVE FEED | TC: {int(t // 60):02d}:{int(t % 60):02d}:{int((t % 1) * 30):02d} | 25.00 FPS"
                cv2.putText(frame, time_code, (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 140, 170), 2, cv2.LINE_AA)

                # Write 5 frames for smoothness
                for _ in range(5):
                    out.write(frame)

            out.release()

        # Generate sample frames at 1 fps for evidence
        for sec in range(0, duration_seconds):
            f_idx = sec * fps
            t = float(sec)
            frame_img = np.zeros((height, width, 3), dtype=np.uint8)
            frame_img[:] = (18, 20, 26)

            cv2.line(frame_img, (100, 700), (400, 300), (32, 36, 48), 2)
            cv2.line(frame_img, (1180, 700), (880, 300), (32, 36, 48), 2)
            cv2.line(frame_img, (400, 300), (880, 300), (32, 36, 48), 2)

            table_x1, table_y1, table_x2, table_y2 = 540, 360, 740, 480
            cv2.rectangle(frame_img, (table_x1, table_y1), (table_x2, table_y2), (45, 52, 68), -1)
            cv2.rectangle(frame_img, (table_x1, table_y1), (table_x2, table_y2), (70, 80, 105), 2)

            if t < 37.0:
                box_x, box_y = 620, 335
                cv2.rectangle(frame_img, (box_x, box_y), (box_x + 50, box_y + 35), (35, 45, 215), -1)
            elif t < 58.0:
                p_pos_x = 200 + min(420, (t - 5.0) * 20) if t < 37.0 else 620 + (t - 37.0) * 18
                box_x = int(p_pos_x + 25)
                box_y = int(320 + math.sin(t * 4) * 8)
                cv2.rectangle(frame_img, (box_x, box_y), (box_x + 50, box_y + 35), (35, 45, 215), -1)

            if 5.0 <= t <= 58.0:
                px = int(150 + ((t - 5.0) / 30.0) * 450) if t < 35.0 else (600 if t <= 42.0 else int(600 + ((t - 42.0) / 16.0) * 600))
                py = 280
                cv2.circle(frame_img, (px + 30, py + 25), 20, (180, 190, 205), -1)
                cv2.line(frame_img, (px + 30, py + 45), (px + 30, py + 140), (160, 175, 195), 10)

            time_code = f"DEMO KEYFRAME {sec:02d}s | EVIDENCE RECORD | SIGNAL INTELLIGENCE"
            cv2.putText(frame_img, time_code, (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 140, 170), 2, cv2.LINE_AA)

            frame_file = frames_dir / f"frame_{sec:06d}.jpg"
            cv2.imwrite(str(frame_file), frame_img, [cv2.IMWRITE_JPEG_QUALITY, 85])

        # Record video in database
        metadata = {
            "duration": float(duration_seconds),
            "fps": float(fps),
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "codec": "h264",
            "file_size": int(demo_video_path.stat().st_size) if demo_video_path.exists() else 1024000
        }
        DatabaseManager.insert_video(
            video_id=DEMO_VIDEO_ID,
            filename="demo_controlled_lab.mp4",
            filepath=str(demo_video_path),
            file_size=metadata["file_size"],
            metadata=metadata,
            is_demo=True
        )

        # Precompute real structured events according to schema
        demo_events = [
            {
                "id": "ev_demo_01",
                "video_id": DEMO_VIDEO_ID,
                "timestamp_start": 5.0,
                "timestamp_end": 7.5,
                "title": "Person #01 enters scene",
                "description": "Person #01 enters the monitored laboratory area from the left perimeter.",
                "importance": "medium",
                "confidence": 0.96,
                "subjects": ["person_1"],
                "objects": [],
                "evidence_frames": [5, 6, 7]
            },
            {
                "id": "ev_demo_02",
                "video_id": DEMO_VIDEO_ID,
                "timestamp_start": 15.0,
                "timestamp_end": 20.0,
                "title": "Person #01 approaches table",
                "description": "Person #01 moves directly toward the central pedestal holding the red container.",
                "importance": "medium",
                "confidence": 0.94,
                "subjects": ["person_1"],
                "objects": ["table"],
                "evidence_frames": [15, 17, 19]
            },
            {
                "id": "ev_demo_03",
                "video_id": DEMO_VIDEO_ID,
                "timestamp_start": 37.0,
                "timestamp_end": 42.0,
                "title": "Object picked up: Red box",
                "description": "Person #01 reaches toward the table, grasps the red box, lifts it, and prepares to move away.",
                "importance": "high",
                "confidence": 0.91,
                "subjects": ["person_1"],
                "objects": ["red_box", "table"],
                "evidence_frames": [37, 39, 41]
            },
            {
                "id": "ev_demo_04",
                "video_id": DEMO_VIDEO_ID,
                "timestamp_start": 45.0,
                "timestamp_end": 52.0,
                "title": "Carrying object across area",
                "description": "Person #01 walks across the monitored field of view carrying the red box in their hands.",
                "importance": "medium",
                "confidence": 0.89,
                "subjects": ["person_1"],
                "objects": ["red_box"],
                "evidence_frames": [45, 48, 51]
            },
            {
                "id": "ev_demo_05",
                "video_id": DEMO_VIDEO_ID,
                "timestamp_start": 55.0,
                "timestamp_end": 58.5,
                "title": "Person #01 exits scene with object",
                "description": "Person #01 exits through the right perimeter carrying the red box.",
                "importance": "high",
                "confidence": 0.95,
                "subjects": ["person_1"],
                "objects": ["red_box"],
                "evidence_frames": [55, 57, 58]
            }
        ]
        DatabaseManager.save_events(DEMO_VIDEO_ID, demo_events)

        # Precompute detections & pose skeleton stream for demo video
        for sec in range(0, duration_seconds):
            t = float(sec)
            boxes = []
            skeletons = []

            # Table box
            boxes.append({
                "box_id": f"box_table_{sec}",
                "track_id": 2,
                "class_id": 60,
                "class_name": "dining table",
                "confidence": 0.92,
                "bbox_normalized": [0.42, 0.50, 0.58, 0.67] # [x1, y1, x2, y2]
            })

            # Red box
            if t < 37.0:
                boxes.append({
                    "box_id": f"box_red_{sec}",
                    "track_id": 3,
                    "class_id": 26,
                    "class_name": "red box",
                    "confidence": 0.93,
                    "bbox_normalized": [0.48, 0.46, 0.52, 0.51]
                })
            elif t <= 58.0:
                p_norm_x = (150 + ((t - 5.0) / 30.0) * 450) / width if t < 35.0 else (600 / width if t <= 42.0 else (600 + ((t - 42.0) / 16.0) * 600) / width)
                boxes.append({
                    "box_id": f"box_red_{sec}",
                    "track_id": 3,
                    "class_name": "red box",
                    "class_id": 26,
                    "confidence": 0.91,
                    "bbox_normalized": [round(p_norm_x + 0.02, 3), 0.44, round(p_norm_x + 0.06, 3), 0.49]
                })

            # Person detection & 17-point pose skeleton
            if 5.0 <= t <= 58.0:
                p_x_px = int(150 + ((t - 5.0) / 30.0) * 450) if t < 35.0 else (600 if t <= 42.0 else int(600 + ((t - 42.0) / 16.0) * 600))
                p_norm_x1 = round((p_x_px) / width, 3)
                p_norm_x2 = round((p_x_px + 60) / width, 3)
                p_norm_y1 = round(280 / height, 3)
                p_norm_y2 = round(520 / height, 3)

                boxes.append({
                    "box_id": f"box_person_{sec}",
                    "track_id": 1,
                    "class_id": 0,
                    "class_name": "person",
                    "confidence": 0.97,
                    "bbox_normalized": [p_norm_x1, p_norm_y1, p_norm_x2, p_norm_y2]
                })

                # Accurate human pose joints
                cx = (p_norm_x1 + p_norm_x2) / 2
                kpts = [
                    {"id": 0, "name": "nose", "x": cx, "y": 0.42, "confidence": 0.98},
                    {"id": 1, "name": "left_eye", "x": cx - 0.005, "y": 0.415, "confidence": 0.97},
                    {"id": 2, "name": "right_eye", "x": cx + 0.005, "y": 0.415, "confidence": 0.97},
                    {"id": 3, "name": "left_ear", "x": cx - 0.01, "y": 0.42, "confidence": 0.95},
                    {"id": 4, "name": "right_ear", "x": cx + 0.01, "y": 0.42, "confidence": 0.95},
                    {"id": 5, "name": "left_shoulder", "x": cx - 0.02, "y": 0.46, "confidence": 0.96},
                    {"id": 6, "name": "right_shoulder", "x": cx + 0.02, "y": 0.46, "confidence": 0.96},
                    {"id": 7, "name": "left_elbow", "x": cx - 0.03, "y": 0.52, "confidence": 0.94},
                    {"id": 8, "name": "right_elbow", "x": cx + 0.03 if t < 37 else cx + 0.01, "y": 0.52 if t < 37 else 0.48, "confidence": 0.94},
                    {"id": 9, "name": "left_wrist", "x": cx - 0.025, "y": 0.58, "confidence": 0.92},
                    {"id": 10, "name": "right_wrist", "x": cx + 0.025 if t < 37 else cx + 0.03, "y": 0.58 if t < 37 else 0.47, "confidence": 0.92},
                    {"id": 11, "name": "left_hip", "x": cx - 0.015, "y": 0.59, "confidence": 0.96},
                    {"id": 12, "name": "right_hip", "x": cx + 0.015, "y": 0.59, "confidence": 0.96},
                    {"id": 13, "name": "left_knee", "x": cx - 0.015, "y": 0.66, "confidence": 0.95},
                    {"id": 14, "name": "right_knee", "x": cx + 0.015, "y": 0.66, "confidence": 0.95},
                    {"id": 15, "name": "left_ankle", "x": cx - 0.015, "y": 0.72, "confidence": 0.94},
                    {"id": 16, "name": "right_ankle", "x": cx + 0.015, "y": 0.72, "confidence": 0.94},
                ]
                skeletons.append({
                    "track_id": 1,
                    "person_id": "person_1",
                    "confidence": 0.96,
                    "keypoints": kpts,
                    "bbox_normalized": [p_norm_x1, p_norm_y1, p_norm_x2, p_norm_y2]
                })

            DatabaseManager.save_detections(DEMO_VIDEO_ID, sec, t, boxes)
            DatabaseManager.save_poses(DEMO_VIDEO_ID, sec, t, skeletons)

        # Save tracks
        tracks = [
            {
                "track_id": 1,
                "class_name": "person",
                "start_time": 5.0,
                "end_time": 58.0,
                "duration": 53.0,
                "total_detections": 54,
                "avg_confidence": 0.97,
                "trajectory": [[float(s), round((150 + ((s - 5.0) / 30.0) * 450) / width, 3), 0.55] for s in range(5, 59)]
            },
            {
                "track_id": 2,
                "class_name": "dining table",
                "start_time": 0.0,
                "end_time": 64.0,
                "duration": 64.0,
                "total_detections": 65,
                "avg_confidence": 0.92,
                "trajectory": [[float(s), 0.58, 0.50] for s in range(0, 65)]
            },
            {
                "track_id": 3,
                "class_name": "red box",
                "start_time": 0.0,
                "end_time": 58.0,
                "duration": 58.0,
                "total_detections": 59,
                "avg_confidence": 0.93,
                "trajectory": [[float(s), 0.50 if s < 37 else round((600 + (s - 37) * 18) / width, 3), 0.48] for s in range(0, 59)]
            }
        ]
        DatabaseManager.save_tracks(DEMO_VIDEO_ID, tracks)

        # Set job as completed
        DatabaseManager.update_job_status(
            job_id="job_demo_01",
            video_id=DEMO_VIDEO_ID,
            status="COMPLETED",
            stage="DONE",
            stage_message="Analysis completed successfully (PRECOMPUTED DEMO DATASET)",
            progress=100.0,
            is_demo=True
        )

        return DEMO_VIDEO_ID
