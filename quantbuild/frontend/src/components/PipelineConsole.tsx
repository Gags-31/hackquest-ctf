import { useEffect, useRef } from "react";
import type { PipelineEvent } from "../types";

const AGENT_ICONS: Record<string, string> = {
  "Project Manager Agent": "🧠",
  "Requirement Agent": "📝",
  "Architecture Agent": "🏗️",
  "Database Agent": "🗄️",
  "API Design Agent": "🔌",
  "UI/UX Agent": "🎨",
  "Frontend Agent": "🖥️",
  "Backend Agent": "⚙️",
  "Testing Agent": "🧪",
  "Debugging Agent": "🐞",
  "Security Agent": "🛡️",
  "Documentation Agent": "📚",
  "Deployment Agent": "🚀",
};

function time(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString([], { hour12: false });
}

export default function PipelineConsole({ events }: { events: PipelineEvent[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) {
    return (
      <div className="text-slate-500 text-sm p-6 text-center">
        Waiting for agent activity…
      </div>
    );
  }

  return (
    <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
      {events.map((ev, i) => (
        <div key={i} className="flex items-start gap-2.5 text-sm group">
          <span className="text-base leading-5 w-6 shrink-0 text-center">
            {AGENT_ICONS[ev.agent] ?? "🤖"}
          </span>
          <div className="min-w-0 flex-1">
            <span className="text-slate-500 text-xs font-mono mr-2">{time(ev.ts)}</span>
            <span className="font-medium text-slate-300">{ev.agent}</span>
            <span
              className={`ml-2 inline-block h-1.5 w-1.5 rounded-full align-middle ${
                ev.status === "failed"
                  ? "bg-red-500"
                  : ev.status === "finished"
                    ? "bg-emerald-500"
                    : ev.status === "started"
                      ? "bg-brand-400 dot-pulse"
                      : "bg-amber-400"
              }`}
            />
            <div className="text-slate-400 text-xs mt-0.5 break-words">{ev.message}</div>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
