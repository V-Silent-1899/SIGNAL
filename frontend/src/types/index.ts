export interface VideoMetadata {
  duration: number;
  fps: number;
  total_frames: number;
  width: number;
  height: number;
  codec?: string;
  file_size: number;
}

export interface Video {
  id: string;
  filename: string;
  file_size: number;
  duration?: number;
  status: string;
  created_at: string;
  metadata?: VideoMetadata;
}

export interface UploadResponse {
  video_id: string;
  filename: string;
  message: string;
  metadata: VideoMetadata;
}

export type AnalysisStage = 
  | "INGESTION" 
  | "EXTRACTION" 
  | "DETECTION" 
  | "TRACKING" 
  | "POSE" 
  | "UNDERSTANDING" 
  | "EVENTS" 
  | "INDEXING" 
  | "DONE"
  | "FAILED";

export interface AnalysisStatus {
  video_id: string;
  job_id: string;
  status: "IDLE" | "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  stage: AnalysisStage;
  progress: number;
  stage_message: string;
  error?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  is_demo: boolean;
}

export interface DetectionBox {
  box_id?: string;
  track_id?: number | null;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox_normalized: [number, number, number, number]; // [x1, y1, x2, y2] in 0.0 - 1.0
}

export interface PoseKeypoint {
  id: number;
  name: string;
  x: number;
  y: number;
  confidence: number;
}

export interface PoseSkeleton {
  track_id?: number | null;
  person_id?: string | null;
  confidence: number;
  keypoints: PoseKeypoint[];
  bbox_normalized?: [number, number, number, number] | null;
}

export interface FrameDetections {
  frame_idx: number;
  timestamp: number;
  boxes: DetectionBox[];
  skeletons: PoseSkeleton[];
}

export interface TrackItem {
  track_id: number;
  class_name: string;
  start_time: number;
  end_time: number;
  duration: number;
  total_detections: number;
  avg_confidence: number;
  trajectory: [number, number, number][]; // [timestamp, x_center, y_center]
}

export interface EventItem {
  id: string;
  video_id: string;
  timestamp_start: number;
  timestamp_end: number;
  title: string;
  description: string;
  importance: "high" | "medium" | "low";
  confidence: number;
  subjects: string[];
  objects: string[];
  evidence_frames: number[];
  evidence_urls: string[];
  created_at?: string;
}

export interface EvidenceItem {
  timestamp: number;
  frame_idx: number;
  image_url: string;
  description: string;
}

export interface QuestionResponse {
  question: string;
  answer: string;
  confidence: number;
  timestamps: number[];
  primary_timestamp?: number | null;
  related_event_ids: string[];
  evidence: EvidenceItem[];
  explanation: string;
}

export interface ModelStatus {
  name: string;
  status: "ONLINE" | "DEGRADED" | "OFFLINE";
  version?: string;
  device?: string;
  details?: string;
}

export interface SystemStatus {
  status: "ONLINE" | "DEGRADED" | "OFFLINE";
  gpu_available: boolean;
  gpu_name?: string | null;
  vram_mb?: number | null;
  cpu_count: number;
  ram_gb: number;
  ffmpeg_available: boolean;
  ffmpeg_path?: string | null;
  models: ModelStatus[];
}
