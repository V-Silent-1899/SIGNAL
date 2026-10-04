import React from "react";
import { Clock } from "lucide-react";
import type { EventItem } from "../types";

interface EventTimelineProps {
  events: EventItem[];
  selectedEvent: EventItem | null;
  currentTime: number;
  duration?: number;
  onSelectEvent: (event: EventItem) => void;
}

export const EventTimeline: React.FC<EventTimelineProps> = ({
  events,
  selectedEvent,
  currentTime,
  onSelectEvent,
}) => {
  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  if (!events || events.length === 0) {
    return (
      <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl p-4 text-center">
        <p className="text-xs font-mono-code text-[#585e72]">
          NO EVENTS EXTRACTED YET. RUN ANALYSIS TO POPULATE TIMELINE.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="font-mono-code text-xs font-bold text-white tracking-wider">
            SEARCHABLE EVENT TIMELINE
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 font-mono-code">
            {events.length} EVENTS
          </span>
        </div>
        <span className="text-xs font-mono-code text-[#8c93a8]">
          CLICK EVENT TO JUMP VIDEO
        </span>
      </div>

      {/* Horizontal Event Cards Grid */}
      <div className="flex items-stretch space-x-3 overflow-x-auto pb-2 pt-1 scrollbar-thin">
        {events.map((ev) => {
          const isSelected = selectedEvent?.id === ev.id;
          const isCurrent =
            currentTime >= ev.timestamp_start && currentTime <= ev.timestamp_end;

          return (
            <div
              key={ev.id}
              onClick={() => onSelectEvent(ev)}
              className={`min-w-[210px] max-w-[240px] p-3 rounded-lg border transition-all cursor-pointer flex flex-col justify-between space-y-2 select-none ${
                isSelected
                  ? "bg-cyan-950/40 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)] scale-[1.02]"
                  : isCurrent
                  ? "bg-[#161822] border-amber-500/50"
                  : "bg-[#0d0f15] border-[#272a3b] hover:border-[#3b425a] hover:bg-[#12141e]"
              }`}
            >
              <div>
                <div className="flex items-center justify-between text-[11px] font-mono-code mb-1">
                  <span className="text-cyan-400 font-semibold">
                    {formatTime(ev.timestamp_start)} - {formatTime(ev.timestamp_end)}
                  </span>
                  <span
                    className={`text-[9px] px-1.5 py-0.2 rounded font-bold uppercase ${
                      ev.importance === "high"
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                        : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    }`}
                  >
                    {ev.importance}
                  </span>
                </div>

                <h4 className="text-xs font-semibold text-white line-clamp-1">
                  {ev.title}
                </h4>

                <p className="text-[11px] text-[#8c93a8] line-clamp-2 mt-1">
                  {ev.description}
                </p>
              </div>

              <div className="flex items-center justify-between pt-1 border-t border-[#1b1e2b] text-[10px] font-mono-code text-[#585e72]">
                <span>CONF: {(ev.confidence * 100).toFixed(0)}%</span>
                <span className="text-cyan-400 hover:underline">JUMP →</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
