export default function Rules() {
  const rules = [
    "Only attack systems explicitly provided for HackQuest CTF. No real targets, no scanning of third-party or college infrastructure.",
    "Never attempt to disrupt the platform itself, other teams, or other participants.",
    "Denial-of-service and distributed denial-of-service traffic of any kind is prohibited.",
    "Flags must not be shared with, or requested from, other teams.",
    "Do not interfere with another team's environment, session or submissions.",
    "Report any infrastructure vulnerability you discover to an organizer instead of exploiting it.",
    "Violations may result in disqualification. The organizing committee has final authority on disputes.",
  ];

  const faqs = [
    {
      q: "How does round progression work?",
      a: "Each challenge you solve reveals a code segment. When every challenge in a round is solved, the segments concatenate in order to form that round's unlock code. You still need an organizer to open the next round, so nobody is rushed.",
    },
    {
      q: "Are hints free?",
      a: "Yes, by default. Each challenge offers three progressive hints at no cost. If the organizers configure a penalty, the cost is shown before you request a hint.",
    },
    {
      q: "Will answers appear on the page?",
      a: "No. Answer keys, unlock codes and hidden tests are never sent to the browser. Round 5 code is parsed and analysed but never executed on the competition server.",
    },
    {
      q: "Why are my points not recorded?",
      a: "Submissions are only accepted while the competition timer is running and your round is open. Check the status banner on the arena page.",
    },
    {
      q: "What counts as a proctoring violation?",
      a: "Leaving fullscreen, switching tabs, minimising the window, or closing the page. Three verified violations trigger an automatic disqualification.",
    },
    {
      q: "A violation was recorded but I did not cheat. What now?",
      a: "Browser events can fire during genuine interruptions such as an OS dialog or a notification. Contact an organizer; forgiveness requires a reason and is recorded in the audit log.",
    },
    {
      q: "Can I switch teams mid-competition?",
      a: "Team membership is fixed once registration closes. Contact an organizer for exceptional cases.",
    },
    {
      q: "How are ties broken?",
      a: "Higher score first, then the team that reached that score earlier, then fewest violations. All timestamps are server-side.",
    },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="h1">Rules &amp; FAQ</h1>
        <p className="muted mt-1">HackQuest CTF 2026 · Pragyan × IEEE-CS KLEIT Chapter</p>
      </div>

      <section>
        <h2 className="h2 mb-3">Code of conduct</h2>
        <ol className="space-y-2">
          {rules.map((r, i) => (
            <li key={i} className="card flex gap-3 py-3">
              <span className="font-mono text-sm font-bold text-neon-cyan">{String(i + 1).padStart(2, "0")}</span>
              <span className="text-sm text-slate-300">{r}</span>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2 className="h2 mb-3">Scoring</h2>
        <div className="card">
          <table className="table">
            <thead><tr><th>Round</th><th>Challenges</th><th>Points each</th></tr></thead>
            <tbody>
              <tr><td>1 · Logic Labyrinth</td><td>3</td><td>100</td></tr>
              <tr><td>2 · Cipher Vault</td><td>3</td><td>200</td></tr>
              <tr><td>3 · Tech Riddles</td><td>4</td><td>300</td></tr>
              <tr><td>4 · Capture The Flag</td><td>4</td><td>400</td></tr>
              <tr><td>5 · The Debug Sprint</td><td>1</td><td>500</td></tr>
            </tbody>
          </table>
          <p className="muted mt-3">
            Tier-weighted totals 4,200 points. Organizers may switch to a normalized mode that
            scales each tier so the maximum is 3,499. The active mode and maximum are always
            displayed in the app.
          </p>
        </div>
      </section>

      <section>
        <h2 className="h2 mb-3">FAQ</h2>
        <div className="space-y-2">
          {faqs.map((f) => (
            <details key={f.q} className="card">
              <summary className="cursor-pointer font-medium text-white">{f.q}</summary>
              <p className="muted mt-2">{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      <section className="card">
        <h2 className="h2 mb-2">Ethical note</h2>
        <p className="muted">
          Round 4 uses a self-contained fictional training lab. Nothing in this competition
          targets a real system, and no real credentials are used anywhere. The debugging round
          is evaluated without executing your code on the server. Hack responsibly — and only
          within the rules of this event.
        </p>
      </section>
    </div>
  );
}