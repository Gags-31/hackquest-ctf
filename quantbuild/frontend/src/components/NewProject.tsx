import { useState } from "react";

const EXAMPLES = [
  {
    label: "🛒 E-Commerce",
    text: "Build an e-commerce platform where customers can browse products, add items to a cart, make payments and track their orders.",
  },
  {
    label: "🏥 Healthcare",
    text: "Create an online healthcare appointment platform where patients can register, search doctors, view available slots and book appointments.",
  },
  {
    label: "📚 Learning",
    text: "Build an online learning platform where instructors publish courses with lessons and students enroll, track progress and leave reviews.",
  },
  {
    label: "✅ Tasks",
    text: "Create a project management tool where teams organize projects, assign tasks with due dates and priorities, and comment on progress.",
  },
  {
    label: "🎟️ Events",
    text: "Build an event ticketing platform where organizers create events and attendees browse events, book tickets and pay online.",
  },
];

export default function NewProject({
  onSubmit,
  busy,
}: {
  onSubmit: (requirement: string, name: string) => void;
  busy: boolean;
}) {
  const [requirement, setRequirement] = useState("");
  const [name, setName] = useState("");

  const canSubmit = requirement.trim().length >= 10 && !busy;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
          Describe the application.
        </h1>
        <p className="text-slate-400 mt-3 text-lg">
          QuantBuild designs, builds, tests and evolves it.
        </p>
      </div>

      <div className="bg-surface-850 border border-surface-800 rounded-xl p-5 shadow-xl">
        <textarea
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          rows={4}
          placeholder="e.g. Build an e-commerce platform where customers can browse products, add items to a cart, make payments and track their orders."
          className="w-full bg-surface-900 border border-surface-800 rounded-lg p-4 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500 resize-none"
        />
        <div className="flex items-center gap-3 mt-4">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Project name (optional)"
            className="flex-1 bg-surface-900 border border-surface-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={() => canSubmit && onSubmit(requirement.trim(), name.trim())}
            disabled={!canSubmit}
            className="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium rounded-lg px-6 py-2.5 text-sm transition"
          >
            {busy ? "Starting…" : "⚡ Build Application"}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mt-5 justify-center">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            onClick={() => setRequirement(ex.text)}
            className="text-xs bg-surface-850 hover:bg-surface-800 border border-surface-800 text-slate-400 hover:text-slate-200 rounded-full px-3.5 py-1.5 transition"
          >
            {ex.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-10 text-center">
        {[
          ["🤖", "12 AI Agents", "specialized pipeline"],
          ["🏗️", "Architecture", "designed, not improvised"],
          ["🧪", "Auto-Tested", "validation + debug loop"],
          ["🚀", "Deploy-Ready", "Docker + CI/CD configs"],
        ].map(([icon, title, sub]) => (
          <div key={title} className="bg-surface-850 border border-surface-800 rounded-lg p-4">
            <div className="text-2xl">{icon}</div>
            <div className="text-sm font-medium text-slate-200 mt-1">{title}</div>
            <div className="text-xs text-slate-500">{sub}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
