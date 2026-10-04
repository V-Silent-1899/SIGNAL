import type {
  Video,
  UploadResponse,
  AnalysisStatus,
  EventItem,
  TrackItem,
  FrameDetections,
  QuestionResponse,
  SystemStatus,
} from "../types";

const BASE_URL = "/api";

export const api = {
  async getHealth(): Promise<{ status: string; app: string }> {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  async getSystemStatus(): Promise<SystemStatus> {
    const res = await fetch(`${BASE_URL}/system/status`);
    if (!res.ok) throw new Error("Failed to load system status");
    return res.json();
  },

  async listVideos(): Promise<Video[]> {
    const res = await fetch(`${BASE_URL}/videos`);
    if (!res.ok) throw new Error("Failed to fetch videos");
    return res.json();
  },

  async getVideo(videoId: string): Promise<Video> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}`);
    if (!res.ok) throw new Error("Failed to fetch video details");
    return res.json();
  },

  async uploadVideo(file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${BASE_URL}/videos/upload`);

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            onProgress(pct);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data);
          } catch (err) {
            reject(new Error("Invalid JSON response from server"));
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || "Upload failed"));
          } catch {
            reject(new Error(`Upload failed with HTTP ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => reject(new Error("Network error during video upload"));

      const formData = new FormData();
      formData.append("file", file);
      xhr.send(formData);
    });
  },

  async startAnalysis(videoId: string): Promise<{ video_id: string; job_id: string; status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/analyze`, {
      method: "POST",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to start analysis");
    }
    return res.json();
  },

  async getAnalysisStatus(videoId: string): Promise<AnalysisStatus> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/status`);
    if (!res.ok) throw new Error("Failed to get analysis status");
    return res.json();
  },

  async getEvents(videoId: string): Promise<{ video_id: string; total_events: number; events: EventItem[] }> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/events`);
    if (!res.ok) throw new Error("Failed to fetch events");
    return res.json();
  },

  async getTracks(videoId: string): Promise<{ video_id: string; total_tracks: number; tracks: TrackItem[] }> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/tracks`);
    if (!res.ok) throw new Error("Failed to fetch tracks");
    return res.json();
  },

  async getDetections(videoId: string): Promise<{ video_id: string; total_frames: number; frames: FrameDetections[] }> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/detections`);
    if (!res.ok) throw new Error("Failed to fetch detections");
    return res.json();
  },

  async askQuestion(videoId: string, question: string): Promise<QuestionResponse> {
    const res = await fetch(`${BASE_URL}/videos/${videoId}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to process question");
    }
    return res.json();
  },

  async loadDemo(): Promise<{ status: string; video_id: string; mode: string; message: string }> {
    const res = await fetch(`${BASE_URL}/demo/load`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to load precomputed demo");
    return res.json();
  },

  getVideoStreamUrl(videoId: string): string {
    return `${BASE_URL}/videos/${videoId}/stream`;
  }
};
