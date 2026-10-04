import React, { useState, useEffect, useRef } from "react";
import { Navbar } from "./components/Navbar";
import { LandingUpload } from "./components/LandingUpload";
import { VideoPlayer } from "./components/VideoPlayer";
import { PipelineProgress } from "./components/PipelineProgress";
import { EventTimeline } from "./components/EventTimeline";
import { EventDetailPanel } from "./components/EventDetailPanel";
import { AskVideoPanel } from "./components/AskVideoPanel";
import { SystemStatusModal } from "./components/SystemStatusModal";
import { api } from "./services/api";
import type {
  Video,
  AnalysisStatus,
  EventItem,
  FrameDetections,
  TrackItem,
  QuestionResponse,
  SystemStatus,
} from "./types";
import {
  Sparkles,
  RotateCcw,
  AlertCircle,
  FileVideo,
} from "lucide-react";

export const App: React.FC = () => {
  // Application State
  const [currentVideo, setCurrentVideo] = useState<Video | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [detections, setDetections] = useState<FrameDetections[]>([]);
  const [tracks, setTracks] = useState<TrackItem[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<EventItem | null>(null);
  const [qaResponse, setQaResponse] = useState<QuestionResponse | null>(null);

  // UI Interactive State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isAsking, setIsAsking] = useState(false);
  const [isSystemModalOpen, setIsSystemModalOpen] = useState(false);
  const [seekTimestamp, setSeekTimestamp] = useState<number | null>(null);
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Poll analysis status ref
  const pollIntervalRef = useRef<number | null>(null);

  // Initial load: Fetch system telemetry
  useEffect(() => {
    loadSystemStatus();
  }, []);

  const loadSystemStatus = async () => {
    try {
      const status = await api.getSystemStatus();
      setSystemStatus(status);
    } catch (e) {
      console.warn("Could not load system status:", e);
    }
  };

  // Poll analysis status while running
  useEffect(() => {
    if (!currentVideo) return;

    const checkStatus = async () => {
      try {
        const st = await api.getAnalysisStatus(currentVideo.id);
        setAnalysisStatus(st);

        if (st.status === "COMPLETED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          // Load generated intelligence
          loadVideoIntelligence(currentVideo.id);
        } else if (st.status === "FAILED") {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setErrorMessage(st.error || "Analysis pipeline failed.");
        }
      } catch (err) {
        console.warn("Status check failed:", err);
      }
    };

    // Immediate check
    checkStatus();

    // Start polling if processing
    if (analysisStatus?.status === "PROCESSING" || analysisStatus?.status === "PENDING") {
      pollIntervalRef.current = window.setInterval(checkStatus, 1000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [currentVideo, analysisStatus?.status]);

  const loadVideoIntelligence = async (videoId: string) => {
    try {
      const [eventsRes, detsRes, tracksRes] = await Promise.all([
        api.getEvents(videoId),
        api.getDetections(videoId),
        api.getTracks(videoId),
      ]);
      setEvents(eventsRes.events);
      setDetections(detsRes.frames);
      setTracks(tracksRes.tracks);
      if (eventsRes.events.length > 0) {
        setSelectedEvent(eventsRes.events[0]);
      }
    } catch (e) {
      console.error("Failed to load video intelligence:", e);
    }
  };

  // Upload Video Flow
  const handleFileSelected = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      const res = await api.uploadVideo(file, (pct) => setUploadProgress(pct));
      const video: Video = {
        id: res.video_id,
        filename: res.filename,
        file_size: res.metadata.file_size,
        duration: res.metadata.duration,
        status: "UPLOADED",
        created_at: new Date().toISOString(),
        metadata: res.metadata,
      };
      setCurrentVideo(video);
      setIsUploading(false);

      // Automatically initiate live analysis for seamless demo workflow
      await handleStartLiveAnalysis(video.id);
    } catch (err: any) {
      setIsUploading(false);
      setErrorMessage(err.message || "Upload failed");
    }
  };

  // Live Analysis Trigger
  const handleStartLiveAnalysis = async (videoId: string) => {
    try {
      setErrorMessage(null);
      await api.startAnalysis(videoId);
      setAnalysisStatus({
        video_id: videoId,
        job_id: "job_init",
        status: "PROCESSING",
        stage: "INGESTION",
        progress: 10,
        stage_message: "Starting real AI pipeline...",
        is_demo: false,
      });
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to start live analysis");
    }
  };

  // Precomputed Demo Load Trigger
  const handleLoadDemo = async () => {
    setErrorMessage(null);
    try {
      const demoRes = await api.loadDemo();
      const video = await api.getVideo(demoRes.video_id);
      setCurrentVideo(video);
      const st = await api.getAnalysisStatus(video.id);
      setAnalysisStatus(st);
      await loadVideoIntelligence(video.id);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load precomputed demo");
    }
  };

  // Natural Language Video Q&A
  const handleAskQuestion = async (question: string) => {
    if (!currentVideo) return;
    setIsAsking(true);
    try {
      const resp = await api.askQuestion(currentVideo.id, question);
      setQaResponse(resp);
      if (resp.primary_timestamp !== null && resp.primary_timestamp !== undefined) {
        setSeekTimestamp(resp.primary_timestamp);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to answer question");
    } finally {
      setIsAsking(false);
    }
  };

  const handleReset = () => {
    setCurrentVideo(null);
    setAnalysisStatus(null);
    setEvents([]);
    setDetections([]);
    setTracks([]);
    setSelectedEvent(null);
    setQaResponse(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-[#f0f2f8] flex flex-col workstation-grid">
      {/* Top Header */}
      <Navbar
        systemStatus={systemStatus}
        isDemo={Boolean(analysisStatus?.is_demo)}
        onOpenSystemModal={() => setIsSystemModalOpen(true)}
        onLoadDemo={handleLoadDemo}
        onReset={handleReset}
      />

      {/* Main Workspace Body */}
      <main className="flex-1 flex flex-col p-4 max-w-7xl mx-auto w-full space-y-4">
        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs font-mono-code">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-[#8c93a8] hover:text-white px-2 py-0.5 rounded cursor-pointer"
            >
              DISMISS
            </button>
          </div>
        )}

        {/* Landing Empty State / Upload Dropzone */}
        {!currentVideo ? (
          <LandingUpload
            onFileSelected={handleFileSelected}
            onLoadDemo={handleLoadDemo}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
          />
        ) : (
          <div className="flex-1 flex flex-col space-y-4">
            {/* Top Workspace Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg bg-[#0f1118] border border-[#272a3b]">
              <div className="flex items-center space-x-3">
                <FileVideo className="w-5 h-5 text-cyan-400" />
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-white font-mono-code truncate max-w-xs">
                      {currentVideo.filename}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#1b1e2b] text-[#8c93a8] font-mono-code">
                      {currentVideo.duration ? `${currentVideo.duration.toFixed(1)}s` : "VIDEO"}
                    </span>
                    {analysisStatus?.is_demo && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950/50 border border-amber-500/30 text-amber-300 font-mono-code">
                        PRECOMPUTED DEMO
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-[#8c93a8]">
                    {tracks.length} Tracks Identified • {events.length} Structured Events
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">
                {analysisStatus?.status !== "PROCESSING" && (
                  <button
                    onClick={() => handleStartLiveAnalysis(currentVideo.id)}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-mono-code text-xs font-semibold cursor-pointer transition-all"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>RUN LIVE ANALYSIS</span>
                  </button>
                )}

                <button
                  onClick={handleReset}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-[#161822] hover:bg-[#1f2233] border border-[#272a3b] text-[#8c93a8] hover:text-white font-mono-code text-xs cursor-pointer transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>NEW VIDEO</span>
                </button>
              </div>
            </div>

            {/* Pipeline Progress Display */}
            {analysisStatus && analysisStatus.status === "PROCESSING" && (
              <PipelineProgress status={analysisStatus} />
            )}

            {/* Center + Right Primary Intelligence Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
              {/* Center Video Surface (7 cols on lg) */}
              <div className="lg:col-span-7 flex flex-col space-y-4">
                <VideoPlayer
                  streamUrl={api.getVideoStreamUrl(currentVideo.id)}
                  duration={currentVideo.duration || 60}
                  detections={detections}
                  events={events}
                  selectedEvent={selectedEvent}
                  seekTimestamp={seekTimestamp}
                  onTimeUpdate={(t) => setCurrentPlaybackTime(t)}
                  onEventClick={(ev) => {
                    setSelectedEvent(ev);
                    setSeekTimestamp(ev.timestamp_start);
                  }}
                />

                {/* Horizontal Event Timeline */}
                <EventTimeline
                  events={events}
                  selectedEvent={selectedEvent}
                  currentTime={currentPlaybackTime}
                  duration={currentVideo.duration || 60}
                  onSelectEvent={(ev) => {
                    setSelectedEvent(ev);
                    setSeekTimestamp(ev.timestamp_start);
                  }}
                />
              </div>

              {/* Right Intelligence & Q&A Panel (5 cols on lg) */}
              <div className="lg:col-span-5 flex flex-col space-y-4">
                {/* Natural Language Video Q&A */}
                <AskVideoPanel
                  onAsk={handleAskQuestion}
                  isLoading={isAsking}
                  response={qaResponse}
                  onJumpToEvidence={(ts) => setSeekTimestamp(ts)}
                />

                {/* Event Deep-Dive Panel */}
                <EventDetailPanel
                  event={selectedEvent}
                  onClose={() => setSelectedEvent(null)}
                  onPlayEvent={(ts) => setSeekTimestamp(ts)}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* System & Model Telemetry Modal */}
      <SystemStatusModal
        status={systemStatus}
        isOpen={isSystemModalOpen}
        onClose={() => setIsSystemModalOpen(false)}
      />
    </div>
  );
};

export default App;
