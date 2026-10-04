import React, { useState } from "react";
import { Sparkles, Send, ArrowRight, CheckCircle, Clock, Loader2 } from "lucide-react";
import type { QuestionResponse } from "../types";

interface AskVideoPanelProps {
  onAsk: (question: string) => Promise<void>;
  isLoading: boolean;
  response: QuestionResponse | null;
  onJumpToEvidence: (timestamp: number) => void;
}

const EXAMPLE_QUESTIONS = [
  "When did the person pick up the red box?",
  "How many people entered?",
  "Find every interaction with the red box.",
  "When did person #01 exit?",
];

export const AskVideoPanel: React.FC<AskVideoPanelProps> = ({
  onAsk,
  isLoading,
  response,
  onJumpToEvidence,
}) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onAsk(query.trim());
  };

  const handleSelectExample = (q: string) => {
    setQuery(q);
    onAsk(q);
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="bg-[#0f1118] border border-[#272a3b] rounded-xl p-5 space-y-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Sparkles className="w-4 h-4 text-cyan-400" />
        <h3 className="font-mono-code text-xs font-bold text-white tracking-wider">
          ASK THE VIDEO (NATURAL LANGUAGE INTELLIGENCE)
        </h3>
      </div>

      {/* Input Field */}
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask anything about this video..."
          disabled={isLoading}
          className="w-full bg-[#090a0f] border border-[#272a3b] focus:border-cyan-400 rounded-lg px-4 py-2.5 pr-10 text-xs text-white placeholder-[#585e72] font-mono-code outline-none transition-all shadow-inner"
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-2 top-0 bottom-0 my-auto p-1.5 rounded hover:bg-cyan-500/20 text-cyan-400 disabled:text-[#3b425a] transition-colors cursor-pointer"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>

      {/* Quick Example Question Chips */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono-code text-[#585e72]">EXAMPLE QUERIES:</span>
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectExample(q)}
              disabled={isLoading}
              className="text-[11px] font-mono-code px-2.5 py-1 rounded bg-[#161822] hover:bg-[#1f2233] border border-[#272a3b] text-[#8c93a8] hover:text-cyan-300 transition-all text-left cursor-pointer"
            >
              "{q}"
            </button>
          ))}
        </div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="py-6 flex flex-col items-center justify-center space-y-2 border border-dashed border-[#272a3b] rounded-lg">
          <Loader2 className="w-6 h-6 text-cyan-400 animate-spin" />
          <p className="text-xs font-mono-code text-cyan-300 tracking-wider">
            SEARCHING VIDEO MEMORY & CORRELATING EVIDENCE...
          </p>
        </div>
      )}

      {/* Answer Result Display */}
      {response && !isLoading && (
        <div className="p-4 rounded-lg bg-[#0d0f17] border border-cyan-500/30 space-y-3 animate-fade-in shadow-[0_0_20px_rgba(34,211,238,0.1)]">
          <div className="flex items-center justify-between text-xs font-mono-code">
            <span className="text-cyan-400 font-semibold flex items-center space-x-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              <span>AI RESPONSE</span>
            </span>
            <span className="text-emerald-400">
              CONFIDENCE: {(response.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <p className="text-sm text-white font-medium leading-relaxed">
            {response.answer}
          </p>

          {response.explanation && (
            <p className="text-xs text-[#8c93a8] leading-relaxed border-t border-[#1b1e2b] pt-2">
              <strong className="text-[#cfd5e6]">Grounding Rationale: </strong>
              {response.explanation}
            </p>
          )}

          {/* Jump to Evidence Action */}
          {response.primary_timestamp !== null && response.primary_timestamp !== undefined && (
            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => onJumpToEvidence(response.primary_timestamp!)}
                className="flex items-center space-x-2 px-3 py-1.5 rounded-md bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 font-mono-code text-xs font-semibold tracking-wider hover:shadow-[0_0_12px_rgba(34,211,238,0.25)] transition-all cursor-pointer"
              >
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>JUMP TO EVIDENCE ({formatTime(response.primary_timestamp!)})</span>
                <ArrowRight className="w-3 h-3 ml-1" />
              </button>

              {response.evidence && response.evidence.length > 0 && (
                <div className="text-[10px] font-mono-code text-[#585e72]">
                  {response.evidence.length} KEYFRAME(S) VERIFIED
                </div>
              )}
            </div>
          )}

          {/* Evidence Frame Thumbnail Preview */}
          {response.evidence && response.evidence.length > 0 && (
            <div className="pt-2 border-t border-[#1b1e2b]">
              <div className="flex items-center space-x-2 overflow-x-auto pb-1">
                {response.evidence.map((ev, i) => (
                  <div
                    key={i}
                    onClick={() => onJumpToEvidence(ev.timestamp)}
                    className="group relative rounded overflow-hidden border border-[#272a3b] hover:border-cyan-400 cursor-pointer bg-black w-24 aspect-video shrink-0"
                  >
                    <img
                      src={ev.image_url}
                      alt={ev.description}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    />
                    <div className="absolute bottom-0 inset-x-0 bg-black/80 px-1 py-0.2 text-[8px] font-mono-code text-cyan-300 text-center">
                      {formatTime(ev.timestamp)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
