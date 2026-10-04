import re
import uuid
from typing import Dict, Any, List, Optional
from backend.app.models.database import DatabaseManager
from backend.app.schemas.qa import QuestionResponse, EvidenceItem

class VideoQAService:
    @staticmethod
    def answer_question(video_id: str, question: str) -> QuestionResponse:
        """
        Answers natural language questions using analyzed events, tracks, and evidence frames.
        Returns precise answers with timestamps, evidence links, and confidence scores.
        """
        events = DatabaseManager.get_events(video_id)
        tracks = DatabaseManager.get_tracks(video_id)
        detections = DatabaseManager.get_detections(video_id)

        q_lower = question.lower()
        person_tracks = [t for t in tracks if t["class_name"] == "person"]
        object_tracks = [t for t in tracks if t["class_name"] != "person"]

        matched_events: List[Dict[str, Any]] = []
        best_event = None
        highest_score = 0.0

        # Keyword & semantic relevance scoring against events
        tokens = re.findall(r"\w+", q_lower)
        stopwords = {"when", "did", "the", "a", "an", "what", "how", "many", "is", "was", "where", "who", "at", "in", "on", "of", "to"}
        key_tokens = [t for t in tokens if t not in stopwords]

        for ev in events:
            score = 0.0
            ev_text = f"{ev['title']} {ev['description']} {' '.join(ev.get('subjects', []))} {' '.join(ev.get('objects', []))}".lower()
            
            for kt in key_tokens:
                if kt in ev_text:
                    score += 1.0

            # Boost specific interaction phrases
            if ("pick" in q_lower or "lift" in q_lower) and ("pick" in ev_text or "interact" in ev_text):
                score += 2.0
            if ("enter" in q_lower or "come in" in q_lower) and "enter" in ev_text:
                score += 2.0
            if ("exit" in q_lower or "leave" in q_lower) and "exit" in ev_text:
                score += 2.0

            if score > 0:
                matched_events.append((score, ev))
                if score > highest_score:
                    highest_score = score
                    best_event = ev

        # Sort matched events by score
        matched_events.sort(key=lambda x: x[0], reverse=True)

        # 1. Handle Count Questions ("How many people...")
        if "how many people" in q_lower or "how many person" in q_lower:
            num_people = len(person_tracks)
            if num_people == 0:
                ans = "No individuals were detected in this video."
                primary_ts = 0.0
                timestamps = []
            elif num_people == 1:
                p = person_tracks[0]
                ans = f"1 person (Person #{p['track_id']:02d}) was observed, present from {p['start_time']:.1f}s to {p['end_time']:.1f}s."
                primary_ts = p['start_time']
                timestamps = [p['start_time']]
            else:
                p_ids = [f"Person #{p['track_id']:02d}" for p in person_tracks]
                ans = f"{num_people} people were detected: {', '.join(p_ids)}."
                primary_ts = person_tracks[0]['start_time']
                timestamps = [p['start_time'] for p in person_tracks]

            evidence = [
                EvidenceItem(
                    timestamp=primary_ts,
                    frame_idx=int(round(primary_ts)),
                    image_url=f"/api/videos/{video_id}/frames/frame_{int(round(primary_ts)):06d}.jpg",
                    description=f"Person detection timestamp {primary_ts:.1f}s"
                )
            ]
            
            resp = QuestionResponse(
                question=question,
                answer=ans,
                confidence=0.94,
                timestamps=timestamps,
                primary_timestamp=primary_ts,
                related_event_ids=[e["id"] for _, e in matched_events[:3]],
                evidence=evidence,
                explanation=f"Based on Ultralytics ByteTrack multi-object tracking, {num_people} persistent person track(s) were identified."
            )
            DatabaseManager.save_qa(
                video_id=video_id,
                qa_id=f"qa_{uuid.uuid4().hex[:8]}",
                question=question,
                answer=ans,
                confidence=0.94,
                timestamps=timestamps,
                primary_timestamp=primary_ts,
                related_events=resp.related_event_ids,
                evidence=[e.dict() for e in evidence]
            )
            return resp

        # 2. If a specific event was matched
        if best_event:
            ts_start = best_event["timestamp_start"]
            ts_end = best_event["timestamp_end"]
            conf = best_event["confidence"]
            time_str = f"{int(ts_start // 60):02d}:{int(ts_start % 60):02d}"
            
            # Craft human-readable answer
            if "pick" in q_lower or "box" in q_lower or "interact" in q_lower:
                subj = best_event.get("subjects", ["The person"])[0].replace("_", " #").title()
                obj = ", ".join(best_event.get("objects", ["the object"]))
                ans = f"{subj} picked up {obj} at approximately {time_str} ({ts_start:.1f}s)."
            else:
                ans = f"{best_event['title']} occurred at approximately {time_str} ({ts_start:.1f}s - {ts_end:.1f}s)."

            evidence_items = []
            for ef in best_event.get("evidence_frames", [int(round(ts_start))]):
                evidence_items.append(EvidenceItem(
                    timestamp=float(ef),
                    frame_idx=int(ef),
                    image_url=f"/api/videos/{video_id}/frames/frame_{int(ef):06d}.jpg",
                    description=f"Keyframe evidence at {ef:.1f}s: {best_event['title']}"
                ))

            resp = QuestionResponse(
                question=question,
                answer=ans,
                confidence=conf,
                timestamps=[ts_start, ts_end],
                primary_timestamp=ts_start,
                related_event_ids=[best_event["id"]],
                evidence=evidence_items,
                explanation=best_event["description"]
            )
            DatabaseManager.save_qa(
                video_id=video_id,
                qa_id=f"qa_{uuid.uuid4().hex[:8]}",
                question=question,
                answer=ans,
                confidence=conf,
                timestamps=[ts_start, ts_end],
                primary_timestamp=ts_start,
                related_events=[best_event["id"]],
                evidence=[e.dict() for e in evidence_items]
            )
            return resp

        # 3. Fallback: Search general detections and tracks
        if object_tracks:
            obj_names = list(set(t["class_name"] for t in object_tracks))
            ans = f"I analyzed the video and found detections of {', '.join(obj_names)} and {len(person_tracks)} person(s)."
        else:
            ans = "I analyzed the video memory, but did not find a high-confidence match for that query."

        resp = QuestionResponse(
            question=question,
            answer=ans,
            confidence=0.70,
            timestamps=[],
            primary_timestamp=None,
            related_event_ids=[],
            evidence=[],
            explanation="No direct spatio-temporal event matched the search query."
        )
        return resp
