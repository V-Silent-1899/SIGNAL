import React from "react";
import { CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import type { AnalysisStatus, AnalysisStage } from "../types";

interface PipelineProgressProps {
  status: AnalysisStatus | null;
}

const PIPELINE_STAGES: { key: AnalysisStage; label: string }[] = [
  { key: "INGESTION", label: "VIDEO INGESTION" },
  { key: "EXTRACTION", label: "FRAME EXTRACTION" },
  { key: "DETECTION", label: "OBJECT DETECTION" },
  { key: "TRACKING", label: "PERSON TRACKING" },
  { key: "POSE", label: "POSE ANALYSIS" },
  { key: "UNDERSTANDING", label: "VIDEO UNDERSTANDING" },
  { key: "EVENTS", label: "EVENT EXTRACTION" },
  { key: "INDEXING", label: "SEMANTIC INDEX" },
];

export const PipelineProgress: React.FC<PipelineProgressProps> = ({ status }) => {
  if (!status || status.status === "IDLE") return null;

  const currentIdx = PIPELINE_STAGES.findIndex((s) => s.key === status.stage);
  const isCompleted = status.status === "COMPLETED";
  const isFailed = status.status === "FAILED";

  return (
    <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {isFailed ? (
            <AlertCircle className="w-4 h-4 text-rose-400" />
          ) : isCompleted ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
          )}
          <span className="font-mono-code text-xs font-bold text-white tracking-wider">
            {isFailed
              ? "PIPELINE FAILED"
              : isCompleted
              ? "INTELLIGENCE READY"
              : "EXECUTING AI PIPELINE"}
          </span>
        </div>
        <span className="font-mono-code text-xs text-cyan-400 font-semibold">
          {status.progress.toFixed(0)}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-[#1b1e2b] h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isFailed
              ? "bg-rose-500"
              : isCompleted
              ? "bg-emerald-400"
              : "bg-gradient-to-r from-cyan-500 to-blue-500"
          }`}
          style={{ width: `${status.progress}%` }}
        />
      </div>

      {/* Stage Status Message */}
      <p className="text-xs text-[#8c93a8] font-mono-code truncate">
        {status.stage_message || "Processing video streams..."}
      </p>

      {/* Stages Checklist */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[#1b1e2b]">
        {PIPELINE_STAGES.map((st, idx) => {
          let stageState: "done" | "active" | "pending" = "pending";

          if (isCompleted || idx < currentIdx) {
            stageState = "done";
          } else if (idx === currentIdx && !isFailed) {
            stageState = "active";
          }

          return (
            <div
              key={st.key}
              className={`flex items-center space-x-2 text-[11px] font-mono-code p-1.5 rounded ${
                stageState === "active"
                  ? "bg-cyan-950/40 text-cyan-300 border border-cyan-500/30"
                  : stageState === "done"
                  ? "text-emerald-400"
                  : "text-[#585e72]"
              }`}
            >
              {stageState === "done" && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
              {stageState === "active" && <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />}
              {stageState === "pending" && <Circle className="w-3.5 h-3.5 text-[#3b425a] shrink-0" />}
              <span className="truncate">{st.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
