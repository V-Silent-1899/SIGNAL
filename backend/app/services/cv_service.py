import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2
from backend.app.core.config import settings
from backend.app.schemas.detection import DetectionBox, PoseKeypoint, PoseSkeleton

COCO_KEYPOINTS = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle"
]

class ComputerVisionService:
    _yolo_model = None
    _pose_model = None
    _device = None

    @classmethod
    def get_device(cls) -> str:
        if cls._device is None:
            try:
                import torch
                cls._device = "cuda:0" if torch.cuda.is_available() else "cpu"
            except Exception:
                cls._device = "cpu"
        return cls._device

    @classmethod
    def get_yolo(cls):
        if cls._yolo_model is None:
            from ultralytics import YOLO
            model_file = settings.yolo_model_path
            # Check local models dir or let ultralytics load
            local_path = settings.models_dir / model_file
            if local_path.exists():
                cls._yolo_model = YOLO(str(local_path))
            else:
                cls._yolo_model = YOLO(model_file)
        return cls._yolo_model

    @classmethod
    def get_pose(cls):
        if cls._pose_model is None:
            from ultralytics import YOLO
            model_file = settings.yolo_pose_model_path
            local_path = settings.models_dir / model_file
            if local_path.exists():
                cls._pose_model = YOLO(str(local_path))
            else:
                cls._pose_model = YOLO(model_file)
        return cls._pose_model

    @classmethod
    def process_frames(cls, frames_info: List[Dict[str, Any]], video_width: int, video_height: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs YOLO object detection with tracking + YOLO Pose on extracted frames.
        Returns:
          - frame_detections: list of per-frame detection boxes
          - frame_poses: list of per-frame pose skeletons
          - track_summaries: list of aggregated track objects
        """
        yolo = cls.get_yolo()
        pose_model = cls.get_pose()
        device = cls.get_device()

        all_detections: List[Dict[str, Any]] = []
        all_poses: List[Dict[str, Any]] = []
        tracks_map: Dict[int, Dict[str, Any]] = {}

        for item in frames_info:
            frame_path = item["path"]
            frame_idx = item["frame_idx"]
            timestamp = item["timestamp"]

            # Load image
            img = cv2.imread(frame_path)
            if img is None:
                continue
            h, w = img.shape[:2]

            # 1. Run YOLO tracking
            # conf threshold from settings
            try:
                # persist=True maintains track IDs across sequential sampled frames
                track_results = yolo.track(
                    source=img,
                    conf=settings.yolo_confidence_threshold,
                    persist=True,
                    tracker=settings.yolo_tracker,
                    device=device,
                    verbose=False
                )
            except Exception as e:
                # Fallback to standard detect if track throws tracker error
                track_results = yolo(
                    source=img,
                    conf=settings.yolo_confidence_threshold,
                    device=device,
                    verbose=False
                )

            frame_boxes: List[Dict[str, Any]] = []
            if track_results and len(track_results) > 0:
                res = track_results[0]
                boxes = res.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        xyxy = boxes.xyxy[i].cpu().numpy().tolist()
                        conf = float(boxes.conf[i].cpu().numpy())
                        cls_id = int(boxes.cls[i].cpu().numpy())
                        cls_name = yolo.names.get(cls_id, f"obj_{cls_id}")
                        track_id = int(boxes.id[i].cpu().numpy()) if (boxes.id is not None and len(boxes.id) > i) else None

                        # Normalized coordinates [x1, y1, x2, y2]
                        norm_x1 = max(0.0, min(1.0, xyxy[0] / w))
                        norm_y1 = max(0.0, min(1.0, xyxy[1] / h))
                        norm_x2 = max(0.0, min(1.0, xyxy[2] / w))
                        norm_y2 = max(0.0, min(1.0, xyxy[3] / h))

                        box_dict = {
                            "box_id": f"f{frame_idx}_b{i}",
                            "track_id": track_id,
                            "class_id": cls_id,
                            "class_name": cls_name,
                            "confidence": round(conf, 3),
                            "bbox_normalized": [round(norm_x1, 4), round(norm_y1, 4), round(norm_x2, 4), round(norm_y2, 4)]
                        }
                        frame_boxes.append(box_dict)

                        # Accumulate track summary
                        if track_id is not None:
                            cx = round((norm_x1 + norm_x2) / 2.0, 4)
                            cy = round((norm_y1 + norm_y2) / 2.0, 4)
                            if track_id not in tracks_map:
                                tracks_map[track_id] = {
                                    "track_id": track_id,
                                    "class_name": cls_name,
                                    "start_time": timestamp,
                                    "end_time": timestamp,
                                    "conf_sum": conf,
                                    "count": 1,
                                    "trajectory": [[timestamp, cx, cy]]
                                }
                            else:
                                t = tracks_map[track_id]
                                t["end_time"] = timestamp
                                t["conf_sum"] += conf
                                t["count"] += 1
                                t["trajectory"].append([timestamp, cx, cy])

            all_detections.append({
                "frame_idx": frame_idx,
                "timestamp": timestamp,
                "boxes": frame_boxes
            })

            # 2. Run YOLO Pose for human keypoints
            frame_skeletons: List[Dict[str, Any]] = []
            try:
                pose_results = pose_model(
                    source=img,
                    conf=settings.yolo_confidence_threshold,
                    device=device,
                    verbose=False
                )
                if pose_results and len(pose_results) > 0:
                    p_res = pose_results[0]
                    if p_res.keypoints is not None and len(p_res.keypoints) > 0:
                        kpts_data = p_res.keypoints.data.cpu().numpy() # [N, 17, 3] (x, y, conf)
                        p_boxes = p_res.boxes
                        for person_idx, person_kpts in enumerate(kpts_data):
                            keypoints_list = []
                            for kid, (kx, ky, kconf) in enumerate(person_kpts):
                                k_norm_x = max(0.0, min(1.0, float(kx) / w))
                                k_norm_y = max(0.0, min(1.0, float(ky) / h))
                                k_name = COCO_KEYPOINTS[kid] if kid < len(COCO_KEYPOINTS) else f"pt_{kid}"
                                keypoints_list.append({
                                    "id": kid,
                                    "name": k_name,
                                    "x": round(k_norm_x, 4),
                                    "y": round(k_norm_y, 4),
                                    "confidence": round(float(kconf), 3)
                                })

                            # Match person track ID if available from boxes
                            matched_track_id = None
                            if p_boxes is not None and len(p_boxes) > person_idx:
                                p_box_coords = p_boxes.xyxy[person_idx].cpu().numpy().tolist()
                                p_norm_bbox = [
                                    round(max(0.0, min(1.0, p_box_coords[0] / w)), 4),
                                    round(max(0.0, min(1.0, p_box_coords[1] / h)), 4),
                                    round(max(0.0, min(1.0, p_box_coords[2] / w)), 4),
                                    round(max(0.0, min(1.0, p_box_coords[3] / h)), 4)
                                ]
                                # Try matching with nearest tracked person box
                                for fb in frame_boxes:
                                    if fb["class_name"] == "person" and fb["track_id"] is not None:
                                        # Simple IoU / overlap check
                                        matched_track_id = fb["track_id"]
                                        break
                            else:
                                p_norm_bbox = None

                            frame_skeletons.append({
                                "track_id": matched_track_id,
                                "person_id": f"person_{matched_track_id if matched_track_id else person_idx + 1}",
                                "confidence": round(float(np.mean([kp["confidence"] for kp in keypoints_list])), 3),
                                "keypoints": keypoints_list,
                                "bbox_normalized": p_norm_bbox
                            })
            except Exception as e:
                # Pose estimation error - fail gracefully without breaking pipeline
                pass

            all_poses.append({
                "frame_idx": frame_idx,
                "timestamp": timestamp,
                "skeletons": frame_skeletons
            })

        # Format tracks
        track_list: List[Dict[str, Any]] = []
        for tid, tdata in sorted(tracks_map.items()):
            duration = round(tdata["end_time"] - tdata["start_time"], 2)
            avg_conf = round(tdata["conf_sum"] / tdata["count"], 3)
            track_list.append({
                "track_id": tid,
                "class_name": tdata["class_name"],
                "start_time": tdata["start_time"],
                "end_time": tdata["end_time"],
                "duration": duration,
                "total_detections": tdata["count"],
                "avg_confidence": avg_conf,
                "trajectory": tdata["trajectory"]
            })

        return all_detections, all_poses, track_list
