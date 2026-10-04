import React from "react";
import { Play, FileText, Image as ImageIcon, X } from "lucide-react";
import type { EventItem } from "../types";

interface EventDetailPanelProps {
  event: EventItem | null;
  onClose: () => void;
  onPlayEvent: (timestamp: number) => void;
}

export const EventDetailPanel: React.FC<EventDetailPanelProps> = ({
  event,
  onClose,
  onPlayEvent,
}) => {
  if (!event) return null;

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <span className="text-[10px] font-mono-code text-cyan-400 uppercase tracking-wider">
            EVENT INTELLIGENCE RECORD
          </span>
          <h3 className="text-base font-bold text-white mt-0.5">
            {event.title}
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[#1b1e2b] text-[#585e72] hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Meta Grid */}
      <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-[#0a0c12] border border-[#1e2130] text-xs font-mono-code">
        <div>
          <span className="text-[#585e72]">TIMESTAMP:</span>
          <p className="text-white font-semibold">
            {formatTime(event.timestamp_start)} – {formatTime(event.timestamp_end)}
          </p>
        </div>
        <div>
          <span className="text-[#585e72]">CONFIDENCE:</span>
          <p className="text-emerald-400 font-semibold">
            {(event.confidence * 100).toFixed(0)}%
          </p>
        </div>
        <div>
          <span className="text-[#585e72]">SUBJECT(S):</span>
          <p className="text-cyan-300">
            {event.subjects.length > 0 ? event.subjects.join(", ") : "None"}
          </p>
        </div>
        <div>
          <span className="text-[#585e72]">OBJECT(S):</span>
          <p className="text-amber-300">
            {event.objects.length > 0 ? event.objects.join(", ") : "None"}
          </p>
        </div>
      </div>

      {/* AI Explanation */}
      <div className="space-y-1">
        <span className="text-[11px] font-mono-code text-[#8c93a8] flex items-center space-x-1">
          <FileText className="w-3.5 h-3.5 text-cyan-400" />
          <span>AI EXPLANATION</span>
        </span>
        <p className="text-xs text-[#cfd5e6] bg-[#141620] p-3 rounded-lg border border-[#232738] leading-relaxed">
          "{event.description}"
        </p>
      </div>

      {/* Evidence Frames */}
      {event.evidence_urls && event.evidence_urls.length > 0 && (
        <div className="space-y-2">
          <span className="text-[11px] font-mono-code text-[#8c93a8] flex items-center space-x-1">
            <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>VERIFIED KEYFRAME EVIDENCE</span>
          </span>
          <div className="grid grid-cols-3 gap-2">
            {event.evidence_urls.map((url, i) => (
              <div
                key={i}
                onClick={() => onPlayEvent(event.evidence_frames[i] ?? event.timestamp_start)}
                className="group relative rounded-md overflow-hidden border border-[#272a3b] hover:border-cyan-400 cursor-pointer bg-black aspect-video transition-all"
              >
                <img
                  src={url}
                  alt={`Evidence frame ${i}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
                <div className="absolute bottom-0 inset-x-0 bg-black/70 px-1 py-0.5 text-[9px] font-mono-code text-cyan-300 text-center">
                  FRAME {event.evidence_frames[i] ?? i}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Play Event Button */}
      <button
        onClick={() => onPlayEvent(event.timestamp_start)}
        className="w-full flex items-center justify-center space-x-2 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-mono-code text-xs font-semibold tracking-wider hover:shadow-[0_0_15px_rgba(34,211,238,0.2)] transition-all cursor-pointer"
      >
        <Play className="w-3.5 h-3.5 fill-current" />
        <span>PLAY EVENT (AT {formatTime(event.timestamp_start)})</span>
      </button>
    </div>
  );
};
