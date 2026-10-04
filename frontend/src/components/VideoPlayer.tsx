import React, { useRef, useEffect, useState, useCallback } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Maximize2,
  Tag,
  UserCheck,
  Box,
  Share2,
} from "lucide-react";
import type { FrameDetections, EventItem } from "../types";

interface VideoPlayerProps {
  streamUrl: string;
  duration: number;
  detections: FrameDetections[];
  events: EventItem[];
  selectedEvent: EventItem | null;
  seekTimestamp: number | null;
  onTimeUpdate?: (currentTime: number) => void;
  onEventClick: (event: EventItem) => void;
}

// 17-Keypoint COCO Skeleton bones connections
const SKELETON_CONNECTIONS: [number, number][] = [
  [0, 1], [0, 2], [1, 3], [2, 4], // Face
  [5, 6],                         // Shoulders
  [5, 7], [7, 9],                 // Left arm
  [6, 8], [8, 10],                // Right arm
  [5, 11], [6, 12],               // Torso
  [11, 12],                       // Hips
  [11, 13], [13, 15],             // Left leg
  [12, 14], [14, 16],             // Right leg
];

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  streamUrl,
  duration,
  detections,
  events,
  selectedEvent,
  seekTimestamp,
  onTimeUpdate,
  onEventClick,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [isMuted, setIsMuted] = useState(true);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showSkeletons, setShowSkeletons] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showInteractions, setShowInteractions] = useState(true);

  // Handle external seek requests
  useEffect(() => {
    if (seekTimestamp !== null && videoRef.current) {
      videoRef.current.currentTime = seekTimestamp;
      setCurrentTime(seekTimestamp);
      if (videoRef.current.paused) {
        videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    }
  }, [seekTimestamp]);

  // Main synchronous canvas overlay loop
  const renderOverlay = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Match canvas dimensions to actual displayed video rectangle
    const rect = video.getBoundingClientRect();
    if (canvas.width !== rect.width || canvas.height !== rect.height) {
      canvas.width = rect.width;
      canvas.height = rect.height;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const cTime = video.currentTime;
    setCurrentTime(cTime);
    onTimeUpdate?.(cTime);

    // Find nearest detection frame within ±0.6s
    if (detections && detections.length > 0) {
      let nearestFrame: FrameDetections | null = null;
      let minDiff = 0.65;

      for (const f of detections) {
        const diff = Math.abs(f.timestamp - cTime);
        if (diff < minDiff) {
          minDiff = diff;
          nearestFrame = f;
        }
      }

      if (nearestFrame) {
        const cw = canvas.width;
        const ch = canvas.height;

        // 1. Draw Bounding Boxes
        if (showBoxes && nearestFrame.boxes) {
          nearestFrame.boxes.forEach((b) => {
            const [nx1, ny1, nx2, ny2] = b.bbox_normalized;
            const x = nx1 * cw;
            const y = ny1 * ch;
            const w = (nx2 - nx1) * cw;
            const h = (ny2 - ny1) * ch;

            const isPerson = b.class_name.toLowerCase().includes("person");
            const boxColor = isPerson ? "#22d3ee" : "#10b981"; // cyan for person, emerald for object
            const bgAlpha = isPerson ? "rgba(34, 211, 238, 0.12)" : "rgba(16, 185, 129, 0.12)";

            // Draw bounding box
            ctx.strokeStyle = boxColor;
            ctx.lineWidth = 2;
            ctx.fillStyle = bgAlpha;
            ctx.fillRect(x, y, w, h);
            ctx.strokeRect(x, y, w, h);

            // Corner crosshairs for technical precision aesthetic
            const cornerSize = Math.min(10, w / 4, h / 4);
            ctx.lineWidth = 3;
            // Top-left
            ctx.beginPath();
            ctx.moveTo(x, y + cornerSize); ctx.lineTo(x, y); ctx.lineTo(x + cornerSize, y);
            ctx.stroke();
            // Bottom-right
            ctx.beginPath();
            ctx.moveTo(x + w, y + h - cornerSize); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w - cornerSize, y + h);
            ctx.stroke();

            // Label tag
            if (showLabels) {
              const labelText = isPerson
                ? `PERSON #${(b.track_id ?? 1).toString().padStart(2, "0")} • ${(b.confidence * 100).toFixed(0)}%`
                : `${b.class_name.toUpperCase()} • ${(b.confidence * 100).toFixed(0)}%`;

              ctx.font = "bold 11px ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace";
              const textMetrics = ctx.measureText(labelText);
              const tagWidth = textMetrics.width + 12;
              const tagHeight = 18;
              const tagY = Math.max(0, y - tagHeight);

              ctx.fillStyle = isPerson ? "rgba(8, 51, 68, 0.85)" : "rgba(6, 78, 59, 0.85)";
              ctx.strokeStyle = boxColor;
              ctx.lineWidth = 1;
              ctx.fillRect(x, tagY, tagWidth, tagHeight);
              ctx.strokeRect(x, tagY, tagWidth, tagHeight);

              ctx.fillStyle = "#ffffff";
              ctx.fillText(labelText, x + 6, tagY + 13);
            }
          });
        }

        // 2. Draw Skeletons
        if (showSkeletons && nearestFrame.skeletons) {
          nearestFrame.skeletons.forEach((skel) => {
            const keypoints = skel.keypoints;
            if (!keypoints || keypoints.length === 0) return;

            // Draw bone lines
            ctx.strokeStyle = "rgba(34, 211, 238, 0.75)";
            ctx.lineWidth = 2.5;

            SKELETON_CONNECTIONS.forEach(([i1, i2]) => {
              const kp1 = keypoints.find((k) => k.id === i1);
              const kp2 = keypoints.find((k) => k.id === i2);
              if (kp1 && kp2 && kp1.confidence > 0.25 && kp2.confidence > 0.25) {
                ctx.beginPath();
                ctx.moveTo(kp1.x * cw, kp1.y * ch);
                ctx.lineTo(kp2.x * cw, kp2.y * ch);
                ctx.stroke();
              }
            });

            // Draw glowing joint points
            keypoints.forEach((kp) => {
              if (kp.confidence > 0.25) {
                const kpx = kp.x * cw;
                const kpy = kp.y * ch;

                ctx.fillStyle = "#38bdf8";
                ctx.beginPath();
                ctx.arc(kpx, kpy, 3.5, 0, 2 * Math.PI);
                ctx.fill();

                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1;
                ctx.stroke();
              }
            });
          });
        }

        // 3. Draw Interaction Lines (Person -> Object)
        if (showInteractions && nearestFrame.boxes && nearestFrame.boxes.length > 1) {
          const persons = nearestFrame.boxes.filter((b) => b.class_name.toLowerCase().includes("person"));
          const objects = nearestFrame.boxes.filter((b) => !b.class_name.toLowerCase().includes("person"));

          for (const p of persons) {
            const [px1, py1, px2, py2] = p.bbox_normalized;
            const pcx = ((px1 + px2) / 2) * cw;
            const pcy = ((py1 + py2) / 2) * ch;

            for (const o of objects) {
              const [ox1, oy1, ox2, oy2] = o.bbox_normalized;
              const ocx = ((ox1 + ox2) / 2) * cw;
              const ocy = ((oy1 + oy2) / 2) * ch;

              const dist = Math.hypot((pcx - ocx) / cw, (pcy - ocy) / ch);

              // If within interaction proximity (< 0.25 normalized distance)
              if (dist < 0.25) {
                ctx.save();
                ctx.strokeStyle = "#f59e0b";
                ctx.lineWidth = 1.5;
                ctx.setLineDash([4, 4]);

                ctx.beginPath();
                ctx.moveTo(pcx, pcy);
                ctx.lineTo(ocx, ocy);
                ctx.stroke();

                // Interaction badge
                const midX = (pcx + ocx) / 2;
                const midY = (pcy + ocy) / 2;
                ctx.fillStyle = "rgba(245, 158, 11, 0.9)";
                ctx.fillRect(midX - 35, midY - 9, 70, 18);
                ctx.fillStyle = "#000";
                ctx.font = "bold 9px ui-monospace, SFMono-Regular, monospace";
                ctx.fillText("INTERACTION", midX - 30, midY + 4);
                ctx.restore();
              }
            }
          }
        }
      }
    }
  }, [detections, onTimeUpdate, showBoxes, showSkeletons, showLabels, showInteractions]);

  // RequestAnimationFrame loop when playing
  useEffect(() => {
    let animId: number;
    const loop = () => {
      renderOverlay();
      animId = requestAnimationFrame(loop);
    };

    if (isPlaying) {
      animId = requestAnimationFrame(loop);
    } else {
      renderOverlay();
    }

    return () => cancelAnimationFrame(animId);
  }, [isPlaying, renderOverlay]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = val;
      setCurrentTime(val);
      renderOverlay();
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col bg-[#0f1118] border border-[#272a3b] rounded-xl overflow-hidden shadow-2xl">
      {/* Video Surface Container */}
      <div
        ref={containerRef}
        className="relative aspect-video w-full bg-black flex items-center justify-center overflow-hidden group select-none"
      >
        <video
          ref={videoRef}
          src={streamUrl}
          playsInline
          muted={isMuted}
          onEnded={() => setIsPlaying(false)}
          className="w-full h-full object-contain"
        />

        {/* Synchronized AI Intelligence Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none w-full h-full"
        />

        {/* Live Workstation HUD Tag */}
        <div className="absolute top-3 left-3 flex items-center space-x-2 px-2.5 py-1 rounded bg-[#090a0f]/80 border border-cyan-500/30 text-[11px] font-mono-code text-cyan-300 backdrop-blur-md">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>AI SYNC OVERLAY • {formatTime(currentTime)}</span>
        </div>

        {/* Center Play Button on Pause */}
        {!isPlaying && (
          <button
            onClick={togglePlay}
            className="absolute inset-0 m-auto w-16 h-16 rounded-full bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/50 flex items-center justify-center text-cyan-300 transition-transform hover:scale-110 cursor-pointer shadow-[0_0_25px_rgba(34,211,238,0.3)] backdrop-blur-sm"
          >
            <Play className="w-8 h-8 fill-current ml-1" />
          </button>
        )}
      </div>

      {/* Control Bar */}
      <div className="p-3 bg-[#0d0f15] border-t border-[#272a3b] space-y-2">
        {/* Seek Bar with Event Markers */}
        <div className="relative flex items-center w-full group">
          <input
            type="range"
            min="0"
            max={duration || 100}
            step="0.1"
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1.5 bg-[#252838] rounded-lg appearance-none cursor-pointer accent-cyan-400 hover:h-2 transition-all"
          />

          {/* Event Flags on Seekbar */}
          {duration > 0 &&
            events.map((ev) => {
              const leftPct = (ev.timestamp_start / duration) * 100;
              const isSelected = selectedEvent?.id === ev.id;
              return (
                <div
                  key={ev.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    onEventClick(ev);
                  }}
                  title={`${ev.title} (${formatTime(ev.timestamp_start)})`}
                  className={`absolute top-0 bottom-0 my-auto w-2.5 h-2.5 rounded-full cursor-pointer transition-transform hover:scale-150 z-10 ${
                    isSelected
                      ? "bg-cyan-300 ring-2 ring-cyan-400 ring-offset-1 ring-offset-black scale-125"
                      : ev.importance === "high"
                      ? "bg-rose-400"
                      : "bg-amber-400"
                  }`}
                  style={{ left: `calc(${leftPct}% - 5px)` }}
                />
              );
            })}
        </div>

        {/* Buttons and Overlay Toggles */}
        <div className="flex items-center justify-between text-xs font-mono-code text-[#8c93a8]">
          {/* Left Controls */}
          <div className="flex items-center space-x-3">
            <button
              onClick={togglePlay}
              className="p-1.5 rounded hover:bg-[#1f2233] text-white transition-colors cursor-pointer"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.currentTime = 0;
                  setCurrentTime(0);
                  renderOverlay();
                }
              }}
              className="p-1.5 rounded hover:bg-[#1f2233] text-[#8c93a8] hover:text-white transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => {
                if (videoRef.current) {
                  videoRef.current.muted = !isMuted;
                  setIsMuted(!isMuted);
                }
              }}
              className="p-1.5 rounded hover:bg-[#1f2233] text-[#8c93a8] hover:text-white transition-colors cursor-pointer"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>

            <span className="text-white">
              {formatTime(currentTime)} <span className="text-[#585e72]">/</span> {formatTime(duration)}
            </span>
          </div>

          {/* Right Layer Toggles */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowBoxes(!showBoxes)}
              className={`flex items-center space-x-1 px-2 py-1 rounded border transition-colors cursor-pointer ${
                showBoxes
                  ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300"
                  : "bg-[#161822] border-[#272a3b] text-[#585e72]"
              }`}
              title="Toggle YOLO bounding boxes"
            >
              <Box className="w-3 h-3" />
              <span className="hidden sm:inline">BOXES</span>
            </button>

            <button
              onClick={() => setShowSkeletons(!showSkeletons)}
              className={`flex items-center space-x-1 px-2 py-1 rounded border transition-colors cursor-pointer ${
                showSkeletons
                  ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300"
                  : "bg-[#161822] border-[#272a3b] text-[#585e72]"
              }`}
              title="Toggle Human Pose Skeletons"
            >
              <UserCheck className="w-3 h-3" />
              <span className="hidden sm:inline">POSES</span>
            </button>

            <button
              onClick={() => setShowInteractions(!showInteractions)}
              className={`flex items-center space-x-1 px-2 py-1 rounded border transition-colors cursor-pointer ${
                showInteractions
                  ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                  : "bg-[#161822] border-[#272a3b] text-[#585e72]"
              }`}
              title="Toggle Interaction Vectors"
            >
              <Share2 className="w-3 h-3" />
              <span className="hidden sm:inline">LINKS</span>
            </button>

            <button
              onClick={() => setShowLabels(!showLabels)}
              className={`flex items-center space-x-1 px-2 py-1 rounded border transition-colors cursor-pointer ${
                showLabels
                  ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-300"
                  : "bg-[#161822] border-[#272a3b] text-[#585e72]"
              }`}
              title="Toggle Confidence Labels"
            >
              <Tag className="w-3 h-3" />
              <span className="hidden sm:inline">TAGS</span>
            </button>

            <button
              onClick={() => {
                if (containerRef.current) {
                  if (document.fullscreenElement) {
                    document.exitFullscreen();
                  } else {
                    containerRef.current.requestFullscreen();
                  }
                }
              }}
              className="p-1.5 rounded hover:bg-[#1f2233] text-[#8c93a8] hover:text-white transition-colors cursor-pointer"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
