import React from "react";
import { Activity, Cpu, Sparkles, Video as VideoIcon, Database } from "lucide-react";
import type { SystemStatus } from "../types";

interface NavbarProps {
  systemStatus: SystemStatus | null;
  isDemo: boolean;
  onOpenSystemModal: () => void;
  onLoadDemo: () => void;
  onReset: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  systemStatus,
  isDemo,
  onOpenSystemModal,
  onLoadDemo,
  onReset,
}) => {
  const isOnline = systemStatus?.status === "ONLINE";
  const isDegraded = systemStatus?.status === "DEGRADED";

  return (
    <header className="border-b border-[#272a3b] bg-[#0c0e15]/90 backdrop-blur-md sticky top-0 z-50 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onReset}>
          <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-widest text-white font-mono-code">
                SIGNAL
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded border border-cyan-500/40 text-cyan-300 bg-cyan-950/40 font-mono-code uppercase font-semibold">
                AI WORKSTATION
              </span>
            </div>
            <p className="text-[11px] text-[#8c93a8] tracking-wider uppercase">
              SEE WHAT MATTERS.
            </p>
          </div>
        </div>

        {/* Center Mode Indicator */}
        <div className="hidden md:flex items-center space-x-2">
          {isDemo ? (
            <div className="flex items-center space-x-2 px-3 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono-code">
              <Database className="w-3.5 h-3.5" />
              <span>PRECOMPUTED DEMO ANALYSIS</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 px-3 py-1 rounded-md bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-mono-code">
              <Sparkles className="w-3.5 h-3.5" />
              <span>LIVE AI PIPELINE</span>
            </div>
          )}
        </div>

        {/* Right Actions & Status */}
        <div className="flex items-center space-x-3">
          {/* Quick Demo Button */}
          <button
            onClick={onLoadDemo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#1f2233] border border-[#272a3b] hover:border-amber-500/40 text-xs text-amber-300 hover:text-amber-200 transition-all cursor-pointer font-mono-code"
            title="Load 2-3 minute controlled demo video with precomputed intelligence"
          >
            <VideoIcon className="w-3.5 h-3.5 text-amber-400" />
            <span>LOAD DEMO</span>
          </button>

          {/* System Status Pill */}
          <button
            onClick={onOpenSystemModal}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-[#12141d] hover:bg-[#1a1c29] border border-[#272a3b] transition-all cursor-pointer text-xs font-mono-code"
          >
            <div
              className={`w-2 h-2 rounded-full ${
                isOnline
                  ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                  : isDegraded
                  ? "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]"
                  : "bg-rose-500"
              }`}
            />
            <span className="text-[#8c93a8]">SYSTEM:</span>
            <span
              className={
                isOnline
                  ? "text-emerald-400 font-semibold"
                  : isDegraded
                  ? "text-amber-400 font-semibold"
                  : "text-rose-400 font-semibold"
              }
            >
              {systemStatus?.status || "CHECKING..."}
            </span>
            <Cpu className="w-3.5 h-3.5 text-[#585e72]" />
          </button>
        </div>
      </div>
    </header>
  );
};
