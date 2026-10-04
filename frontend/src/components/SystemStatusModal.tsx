import React from "react";
import { Cpu, CheckCircle2, AlertTriangle, XCircle, X } from "lucide-react";
import type { SystemStatus } from "../types";

interface SystemStatusModalProps {
  status: SystemStatus | null;
  isOpen: boolean;
  onClose: () => void;
}

export const SystemStatusModal: React.FC<SystemStatusModalProps> = ({
  status,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !status) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl max-w-xl w-full p-6 space-y-6 shadow-2xl relative">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-[#272a3b] pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-cyan-950/40 border border-cyan-500/30 text-cyan-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-mono-code text-base font-bold text-white tracking-wide">
                SYSTEM & MODEL TELEMETRY
              </h3>
              <p className="text-xs text-[#8c93a8]">
                Real-time hardware verification and open-weight model status
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[#1f2233] text-[#585e72] hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Hardware Status */}
        <div className="grid grid-cols-2 gap-3 text-xs font-mono-code">
          <div className="p-3 rounded-lg bg-[#090a0f] border border-[#1e2130] space-y-1">
            <span className="text-[#585e72]">ACCELERATOR / GPU</span>
            <p className="text-white font-semibold flex items-center space-x-1.5">
              <span>{status.gpu_name || "CPU Standard Mode"}</span>
            </p>
            <p className="text-[10px] text-[#8c93a8]">
              {status.vram_mb ? `VRAM: ${status.vram_mb} MB` : "Zero-VRAM CPU Fallback Active"}
            </p>
          </div>

          <div className="p-3 rounded-lg bg-[#090a0f] border border-[#1e2130] space-y-1">
            <span className="text-[#585e72]">PROCESSOR & RAM</span>
            <p className="text-white font-semibold">
              {status.cpu_count} CORES • {status.ram_gb} GB RAM
            </p>
            <p className="text-[10px] text-[#8c93a8]">
              FFmpeg: {status.ffmpeg_available ? "VERIFIED ONLINE" : "NOT FOUND"}
            </p>
          </div>
        </div>

        {/* Model Stack */}
        <div className="space-y-2">
          <span className="text-xs font-mono-code text-[#8c93a8] tracking-wider uppercase font-semibold">
            AI & COMPUTER VISION MODELS
          </span>
          <div className="space-y-2">
            {status.models.map((m, idx) => {
              const isOnline = m.status === "ONLINE";
              const isDegraded = m.status === "DEGRADED";

              return (
                <div
                  key={idx}
                  className="flex items-start justify-between p-3 rounded-lg bg-[#0d0f15] border border-[#222536] text-xs font-mono-code"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{m.name}</span>
                      {m.version && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#1c1f2e] text-[#8c93a8]">
                          {m.version}
                        </span>
                      )}
                    </div>
                    {m.details && (
                      <p className="text-[11px] text-[#8c93a8] max-w-sm">
                        {m.details}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0 ml-2">
                    {isOnline && (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>ONLINE</span>
                      </span>
                    )}
                    {isDegraded && (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-950/40 border border-amber-500/30 text-amber-400 text-[10px] font-bold">
                        <AlertTriangle className="w-3 h-3" />
                        <span>DEGRADED</span>
                      </span>
                    )}
                    {!isOnline && !isDegraded && (
                      <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-950/40 border border-rose-500/30 text-rose-400 text-[10px] font-bold">
                        <XCircle className="w-3 h-3" />
                        <span>OFFLINE</span>
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-2 border-t border-[#272a3b] flex items-center justify-between text-xs font-mono-code text-[#585e72]">
          <span>SIGNAL v1.0.0</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-[#1b1e2b] hover:bg-[#252838] text-white transition-colors cursor-pointer"
          >
            DISMISS
          </button>
        </div>
      </div>
    </div>
  );
};
