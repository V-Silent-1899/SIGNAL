import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS videos (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        duration REAL,
        fps REAL,
        total_frames INTEGER,
        width INTEGER,
        height INTEGER,
        file_size INTEGER,
        status TEXT DEFAULT 'UPLOADED',
        is_demo INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS analysis_jobs (
        id TEXT PRIMARY KEY,
        video_id TEXT NOT NULL,
        status TEXT NOT NULL,
        stage TEXT NOT NULL,
        stage_message TEXT,
        progress REAL DEFAULT 0.0,
        error TEXT,
        started_at TEXT,
        completed_at TEXT,
        is_demo INTEGER DEFAULT 0,
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        video_id TEXT NOT NULL,
        timestamp_start REAL NOT NULL,
        timestamp_end REAL NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        importance TEXT DEFAULT 'medium',
        confidence REAL NOT NULL,
        subjects_json TEXT,
        objects_json TEXT,
        evidence_frames_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS detections (
        video_id TEXT NOT NULL,
        frame_idx INTEGER NOT NULL,
        timestamp REAL NOT NULL,
        detections_json TEXT NOT NULL,
        PRIMARY KEY(video_id, frame_idx),
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS poses (
        video_id TEXT NOT NULL,
        frame_idx INTEGER NOT NULL,
        timestamp REAL NOT NULL,
        poses_json TEXT NOT NULL,
        PRIMARY KEY(video_id, frame_idx),
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tracks (
        video_id TEXT NOT NULL,
        track_id INTEGER NOT NULL,
        class_name TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        duration REAL NOT NULL,
        total_detections INTEGER NOT NULL,
        avg_confidence REAL NOT NULL,
        trajectory_json TEXT NOT NULL,
        PRIMARY KEY(video_id, track_id),
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS qa_history (
        id TEXT PRIMARY KEY,
        video_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        confidence REAL NOT NULL,
        timestamps_json TEXT,
        primary_timestamp REAL,
        related_events_json TEXT,
        evidence_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

class DatabaseManager:
    @staticmethod
    def insert_video(video_id: str, filename: str, filepath: str, file_size: int, metadata: Dict[str, Any], is_demo: bool = False):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO videos 
            (id, filename, filepath, duration, fps, total_frames, width, height, file_size, status, is_demo, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            filename,
            filepath,
            metadata.get("duration", 0.0),
            metadata.get("fps", 0.0),
            metadata.get("total_frames", 0),
            metadata.get("width", 0),
            metadata.get("height", 0),
            file_size,
            "UPLOADED",
            1 if is_demo else 0,
            now
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_video(video_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    @staticmethod
    def list_videos() -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def update_job_status(job_id: str, video_id: str, status: str, stage: str, stage_message: str, progress: float, error: Optional[str] = None, is_demo: bool = False):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        completed_at = now if status in ["COMPLETED", "FAILED"] else None
        
        cursor.execute("""
            INSERT INTO analysis_jobs (id, video_id, status, stage, stage_message, progress, error, started_at, completed_at, is_demo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                status=excluded.status,
                stage=excluded.stage,
                stage_message=excluded.stage_message,
                progress=excluded.progress,
                error=excluded.error,
                completed_at=COALESCE(excluded.completed_at, analysis_jobs.completed_at)
        """, (
            job_id, video_id, status, stage, stage_message, progress, error, now, completed_at, 1 if is_demo else 0
        ))
        
        # update video status as well
        cursor.execute("UPDATE videos SET status = ? WHERE id = ?", (status, video_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_job_by_video(video_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_jobs WHERE video_id = ? ORDER BY started_at DESC LIMIT 1", (video_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return dict(row)

    @staticmethod
    def save_events(video_id: str, events: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        for ev in events:
            cursor.execute("""
                INSERT OR REPLACE INTO events 
                (id, video_id, timestamp_start, timestamp_end, title, description, importance, confidence, subjects_json, objects_json, evidence_frames_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ev["id"],
                video_id,
                ev["timestamp_start"],
                ev["timestamp_end"],
                ev["title"],
                ev["description"],
                ev.get("importance", "medium"),
                ev["confidence"],
                json.dumps(ev.get("subjects", [])),
                json.dumps(ev.get("objects", [])),
                json.dumps(ev.get("evidence_frames", [])),
                now
            ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_events(video_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE video_id = ? ORDER BY timestamp_start ASC", (video_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["subjects"] = json.loads(d["subjects_json"]) if d.get("subjects_json") else []
            d["objects"] = json.loads(d["objects_json"]) if d.get("objects_json") else []
            d["evidence_frames"] = json.loads(d["evidence_frames_json"]) if d.get("evidence_frames_json") else []
            results.append(d)
        return results

    @staticmethod
    def save_detections(video_id: str, frame_idx: int, timestamp: float, detections: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO detections (video_id, frame_idx, timestamp, detections_json)
            VALUES (?, ?, ?, ?)
        """, (video_id, frame_idx, timestamp, json.dumps(detections)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_detections(video_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT frame_idx, timestamp, detections_json FROM detections WHERE video_id = ? ORDER BY frame_idx ASC", (video_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            results.append({
                "frame_idx": r["frame_idx"],
                "timestamp": r["timestamp"],
                "boxes": json.loads(r["detections_json"])
            })
        return results

    @staticmethod
    def save_poses(video_id: str, frame_idx: int, timestamp: float, poses: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO poses (video_id, frame_idx, timestamp, poses_json)
            VALUES (?, ?, ?, ?)
        """, (video_id, frame_idx, timestamp, json.dumps(poses)))
        conn.commit()
        conn.close()

    @staticmethod
    def get_poses(video_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT frame_idx, timestamp, poses_json FROM poses WHERE video_id = ? ORDER BY frame_idx ASC", (video_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            results.append({
                "frame_idx": r["frame_idx"],
                "timestamp": r["timestamp"],
                "skeletons": json.loads(r["poses_json"])
            })
        return results

    @staticmethod
    def save_tracks(video_id: str, tracks: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()
        for t in tracks:
            cursor.execute("""
                INSERT OR REPLACE INTO tracks 
                (video_id, track_id, class_name, start_time, end_time, duration, total_detections, avg_confidence, trajectory_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video_id,
                t["track_id"],
                t["class_name"],
                t["start_time"],
                t["end_time"],
                t["duration"],
                t["total_detections"],
                t["avg_confidence"],
                json.dumps(t["trajectory"])
            ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_tracks(video_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tracks WHERE video_id = ? ORDER BY track_id ASC", (video_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["trajectory"] = json.loads(d["trajectory_json"]) if d.get("trajectory_json") else []
            results.append(d)
        return results

    @staticmethod
    def save_qa(video_id: str, qa_id: str, question: str, answer: str, confidence: float, timestamps: List[float], primary_timestamp: Optional[float], related_events: List[str], evidence: List[Dict[str, Any]]):
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO qa_history (id, video_id, question, answer, confidence, timestamps_json, primary_timestamp, related_events_json, evidence_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            qa_id, video_id, question, answer, confidence, json.dumps(timestamps), primary_timestamp, json.dumps(related_events), json.dumps(evidence), now
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_qa_history(video_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM qa_history WHERE video_id = ? ORDER BY created_at DESC", (video_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            d = dict(r)
            d["timestamps"] = json.loads(d["timestamps_json"]) if d.get("timestamps_json") else []
            d["related_event_ids"] = json.loads(d["related_events_json"]) if d.get("related_events_json") else []
            d["evidence"] = json.loads(d["evidence_json"]) if d.get("evidence_json") else []
            results.append(d)
        return results
