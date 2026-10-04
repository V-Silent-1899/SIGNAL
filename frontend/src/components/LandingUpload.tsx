import React, { useRef, useState } from "react";
import { UploadCloud, PlayCircle, ShieldCheck, Zap, Sparkles, CheckCircle2 } from "lucide-react";

interface LandingUploadProps {
  onFileSelected: (file: File) => void;
  onLoadDemo: () => void;
  isUploading: boolean;
  uploadProgress: number;
}

export const LandingUpload: React.FC<LandingUploadProps> = ({
  onFileSelected,
  onLoadDemo,
  isUploading,
  uploadProgress,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 max-w-5xl mx-auto w-full my-auto">
      {/* Hero Headline */}
      <div className="text-center mb-8 space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-400 text-xs font-mono-code mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>REAL OPEN-WEIGHT VIDEO INTELLIGENCE WORKSTATION</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight font-mono-code">
          SIGNAL
        </h1>
        <p className="text-lg md:text-xl font-medium text-cyan-400 tracking-wider">
          SEE WHAT MATTERS.
        </p>
        <p className="text-sm md:text-base text-[#8c93a8] max-w-xl mx-auto">
          Turn video into searchable, explainable events. Detect objects, track people, estimate human poses, and ask natural-language questions with timestamped evidence.
        </p>
      </div>

      {/* Upload Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`w-full max-w-2xl border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer relative overflow-hidden group ${
          isDragOver
            ? "border-cyan-400 bg-cyan-950/20 shadow-[0_0_30px_rgba(34,211,238,0.25)]"
            : "border-[#272a3b] hover:border-cyan-500/50 bg-[#0f1118]/80 hover:bg-[#131622]"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.webm,.mov"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              onFileSelected(e.target.files[0]);
            }
          }}
        />

        {isUploading ? (
          <div className="py-6 space-y-4">
            <div className="w-12 h-12 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-mono-code text-cyan-300">
              UPLOADING & VALIDATING VIDEO... {uploadProgress}%
            </p>
            <div className="w-full bg-[#1b1e2b] h-2 rounded-full overflow-hidden max-w-md mx-auto">
              <div
                className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all duration-200"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-[#8c93a8]">
              Extracting container header and verifying stream integrity
            </p>
          </div>
        ) : (
          <div className="py-4 space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-center mx-auto text-cyan-400 group-hover:scale-105 transition-transform shadow-[0_0_20px_rgba(34,211,238,0.15)]">
              <UploadCloud className="w-8 h-8" />
            </div>

            <div>
              <p className="text-base font-semibold text-white tracking-wide font-mono-code">
                DROP VIDEO HERE
              </p>
              <p className="text-xs text-[#8c93a8] mt-1">
                or <span className="text-cyan-400 underline decoration-cyan-500/40">SELECT VIDEO</span> from your device
              </p>
            </div>

            <div className="flex items-center justify-center space-x-4 text-xs font-mono-code text-[#585e72] pt-2">
              <span>MP4 • WEBM • MOV</span>
              <span>•</span>
              <span>RECOMMENDED: 30s – 5min</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Demonstration Action */}
      <div className="mt-8 flex flex-col items-center space-y-3">
        <div className="flex items-center space-x-2 text-xs text-[#8c93a8]">
          <span>Need an immediate 2-minute hackathon demonstration?</span>
        </div>
        <button
          onClick={onLoadDemo}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-amber-500/20 to-orange-500/20 hover:from-amber-500/30 hover:to-orange-500/30 border border-amber-500/40 text-amber-300 font-mono-code text-xs font-semibold tracking-wider hover:shadow-[0_0_20px_rgba(245,158,11,0.2)] transition-all cursor-pointer"
        >
          <PlayCircle className="w-4 h-4 text-amber-400" />
          <span>LOAD PRECOMPUTED DEMO DATASET</span>
        </button>
      </div>

      {/* Architecture Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl mt-12 text-left">
        <div className="p-4 rounded-lg bg-[#0f1118]/60 border border-[#272a3b] space-y-1.5">
          <div className="flex items-center space-x-2 text-cyan-400 font-mono-code text-xs font-semibold">
            <Zap className="w-3.5 h-3.5" />
            <span>YOLOv8 + ByteTrack</span>
          </div>
          <p className="text-xs text-[#8c93a8]">
            Real open-weight object detection, person identification, and persistent multi-target trajectory tracking.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-[#0f1118]/60 border border-[#272a3b] space-y-1.5">
          <div className="flex items-center space-x-2 text-emerald-400 font-mono-code text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>17-Keypoint Pose</span>
          </div>
          <p className="text-xs text-[#8c93a8]">
            Estimates human skeletal joint dynamics to understand hand-object reach, pickup, and carry interactions.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-[#0f1118]/60 border border-[#272a3b] space-y-1.5">
          <div className="flex items-center space-x-2 text-purple-400 font-mono-code text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Explainable Q&A</span>
          </div>
          <p className="text-xs text-[#8c93a8]">
            Ask questions like "When did the person pick up the red box?" and jump directly to exact timestamped evidence.
          </p>
        </div>
      </div>
    </div>
  );
};
