import { Link } from 'react-router-dom'
import { OrganiserMark } from '../components/Brand'
import { Badge, Countdown, Marquee, SectionTitle, Stat, useEvent } from '../components/Ui'

const categories = [
  ['CRYPTOGRAPHY', 'Classical ciphers, XOR, modular arithmetic and toy public-key systems.', 'neon'],
  ['LOGIC & MISC', 'Patterns, sequences, encodings and reasoning under pressure.', 'cyan'],
  ['PROGRAMMING', 'Algorithms, debugging and constructive problem solving.', 'violet'],
  ['WEB SECURITY', 'Safe, isolated toy applications with synthetic vulnerabilities.', 'amber'],
  ['FORENSICS', 'Magic bytes, metadata, logs and synthetic network captures.', 'cyan'],
  ['OSINT & INVESTIGATION', 'Fictional identities and authorised evidence chains.', 'neon'],
]

const rules = [
  'Teams must contain 2–4 participants and use unique email addresses.',
  'Rounds unlock simultaneously from the organiser console. Future rounds stay locked.',
  'Flags use the HQCTF{...} format and are validated strictly on the server.',
  'Hints never reveal a flag. Hint penalties are configured by the organisers.',
  'All challenges use synthetic, fictional and explicitly authorised data.',
  'No attacks on real websites, public infrastructure or third-party services.',
  'The timer is authoritative server time; refreshing never resets it.',
  'Three proctoring violations may result in disqualification at organiser discretion.',
]

const faqs = [
  ['When is the event?', '25 November 2026, 11:00 AM IST. The countdown above is locked to that date, not to deployment time.'],
  ['Who can participate?', 'Engineering students from all branches. Teams of 2–4 participants.'],
  ['How do rounds work?', 'Four independent stages. Organisers start each round for every approved team at once.'],
  ['Is prior CTF experience needed?', 'No. Round 1 is beginner-friendly and hints are available for every challenge.'],
  ['Are the challenges safe?', 'Yes. Everything is synthetic, self-contained and authorised — no real targets.'],
  ['How are winners decided?', 'Total points across all four rounds, verified by the organisers before publishing.'],
]

export default function Landing() {
  const { event, schedule, marquee } = useEvent()
  return (
    <>
      {/* HERO */}
      <section className="relative mx-auto max-w-7xl px-5 pt-16 pb-12 md:pt-24">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-80 overflow-hidden">
          <div className="scanline" />
        </div>
        <div className="grid items-center gap-12 lg:grid-cols-[1.15fr_.85fr]">
          <div>
            <div className="mb-6 flex flex-wrap items-center gap-3">
              <Badge tone="green">ONLINE · 25 NOV 2026</Badge>
              <Badge tone="cyan">TEAMS OF 2–4</Badge>
              <Badge tone="violet">₹ / GLORY / bragging rights</Badge>
            </div>
            <p className="mb-4 font-mono text-xs uppercase tracking-[.4em] text-cyan">
              Pragyan × IEEE-CS KLEIT Chapter presents
            </p>
            <h1 className="glitch font-display text-6xl font-extrabold leading-[.92] tracking-tight text-white sm:text-7xl lg:text-8xl"
                data-text="HACKQUEST">
              HACK<br /><span className="text-neon">QUEST</span>
              <span className="align-top font-mono text-2xl text-cyan"> 2026</span>
            </h1>
            <p className="mt-6 font-mono text-lg font-bold uppercase tracking-[.18em] text-neon sm:text-2xl">
              BREAK THE TARGET. OWN THE FLAG.
            </p>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-slate-300">
              Four rounds. Forty-eight original challenges. One night to prove you can decode,
              debug, investigate and out-algorithm the competition — entirely inside a safe,
              synthetic cyber range.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register" className="btn btn-primary">REGISTER YOUR TEAM →</Link>
              <Link to="/login" className="btn btn-ghost">TEAM LOGIN</Link>
              <a href="#rules" className="btn btn-ghost">READ THE RULES</a>
            </div>
            <div className="mt-10">
              <div className="mb-3 font-mono text-[10px] uppercase tracking-[.3em] text-slate-500">
                // COUNTDOWN TO INNAUGURATION
              </div>
              <Countdown target={event?.event_datetime} />
            </div>
          </div>

          <div className="glass neon-border relative overflow-hidden rounded-2xl p-5">
            <div className="mb-4 flex items-center gap-2 border-b border-slate-800 pb-3">
              <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
              <span className="h-2.5 w-2.5 rounded-full bg-neon" />
              <span className="ml-2 font-mono text-xs text-slate-400">hackquest@range:~</span>
            </div>
            <pre className="overflow-x-auto font-mono text-[12px] leading-6 text-slate-300">{`> ./hackquest --status

[✓] 4 competition rounds armed
[✓] 48 challenges generated
[✓] 20 cyber riddles loaded
[✓] team access codes: HQ-XXXXXX
[✓] server-authoritative timers
[✓] flags: HQCTF{...}

> whoami
student.engineer

> mission
decode  →  debug  →  detect  →  dominate

> _
`}</pre>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Stat label="ROUNDS" value="04" />
              <Stat label="CHALLENGES" value="48" accent="cyan" />
              <Stat label="MIN TEAM" value="02" accent="violet" />
            </div>
          </div>
        </div>
      </section>

      <Marquee text={marquee || 'CAPTURE THE FLAG • CRYPTOGRAPHY • DIGITAL FORENSICS • OSINT • DEBUGGING • WEB SECURITY • ALGORITHMS • LOGIC • CYBERSECURITY • CTF • CODE • ANALYSE • DECODE'} />

      {/* ABOUT */}
      <section id="about" className="mx-auto max-w-7xl px-5 py-20">
        <SectionTitle kicker="mission brief" title="Not a quiz. A full-spectrum cyber sprint." />
        <div className="grid gap-6 md:grid-cols-2">
          <div className="glass rounded-xl p-6 leading-relaxed text-slate-300">
            <p className="mb-4">
              HackQuest CTF 2026 is a four-hour online capture-the-flag competition where teams
              solve original puzzles across cryptography, logic, debugging, secure code, digital
              forensics, OSINT and algorithms.
            </p>
            <p>
              Every artefact is fictional and purpose-built. No real accounts, public websites or
              college infrastructure are ever in scope — you can focus entirely on the craft.
            </p>
          </div>
          <div className="glass cyan-border rounded-xl p-6">
            <div className="font-mono text-[10px] uppercase tracking-[.25em] text-cyan">Event parameters</div>
            <dl className="mt-4 space-y-3 font-mono text-sm">
              {[
                ['DATE', event?.event_date || '2026-11-25'],
                ['START', (event?.event_start_time || '11:00') + ' IST'],
                ['WINDOW', event?.duration || '4 hours 30 minutes'],
                ['PLAY TIME', event?.competition_duration || '3 hours 45 minutes'],
                ['TEAM', event?.team_size || '2–4 participants'],
                ['FLAG', 'HQCTF{...}'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-slate-800/70 pb-2">
                  <dt className="text-slate-500">{k}</dt><dd className="text-right text-slate-100">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <SectionTitle kicker="attack surface" title="Six disciplines. One scoreboard." />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map(([name, desc, tone], i) => (
            <div key={name} className="glass group rounded-xl p-5 transition hover:-translate-y-1 hover:border-neon/40">
              <div className="mb-3 flex items-center justify-between">
                <span className="font-mono text-2xl font-extrabold text-slate-700">{String(i + 1).padStart(2, '0')}</span>
                <Badge tone={tone as any}>{['8 CHALLENGES'][0]}</Badge>
              </div>
              <h3 className="font-display text-lg font-bold text-white">{name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-400">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ROUNDS */}
      <section id="rounds" className="mx-auto max-w-7xl px-5 py-16">
        <SectionTitle kicker="competition stages" title="Four rounds, released together." />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {[
            ['01', 'LOGIC LAUNCHPAD', '50 MIN', 'Beginner → intermediate. Binary, hex, ciphers, sequences and security terminology.', 'neon'],
            ['02', 'DEBUGGING DEN', '60 MIN', 'Python faults, SQL logic, input validation and toy web vulnerabilities.', 'cyan'],
            ['03', 'DIGITAL DETECTIVES', '60 MIN', 'Synthetic logs, file signatures, metadata, packets and safe OSINT.', 'violet'],
            ['04', 'ALGORITHM SHOWDOWN', '45 MIN', 'Advanced chains: algorithms, crypto puzzles and forensic reasoning.', 'amber'],
          ].map(([n, name, dur, desc, tone]) => (
            <div key={n} className={`glass rounded-xl p-5 ${tone === 'neon' ? 'neon-border' : tone === 'cyan' ? 'cyan-border' : tone === 'violet' ? 'violet-border' : ''}`}>
              <div className="font-mono text-4xl font-extrabold text-slate-700">{n}</div>
              <h3 className="mt-2 font-display text-base font-bold tracking-wide text-white">{name}</h3>
              <div className="mt-2 font-mono text-xs text-neon">{dur}</div>
              <p className="mt-3 text-sm leading-relaxed text-slate-400">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SCHEDULE */}
      <section id="schedule" className="mx-auto max-w-7xl px-5 py-16">
        <SectionTitle kicker="run of show" title="The complete event schedule." />
        <div className="glass overflow-hidden rounded-xl">
          {schedule.length === 0 && <div className="p-6 font-mono text-xs text-slate-500">Loading schedule…</div>}
          {schedule.map((s: any, i: number) => (
            <div key={i} className={`flex flex-col gap-1 border-b border-slate-800/70 px-5 py-4 sm:flex-row sm:items-center sm:justify-between ${i % 2 ? 'bg-slate-950/30' : ''}`}>
              <span className="font-mono text-xs font-bold text-cyan sm:w-52">{s.time}</span>
              <span className={`text-sm ${s.activity.includes('Round') || s.activity.includes('Final') ? 'font-semibold text-neon' : 'text-slate-300'}`}>
                {s.activity}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* RULES */}
      <section id="rules" className="mx-auto max-w-7xl px-5 py-16">
        <SectionTitle kicker="terms of engagement" title="Play fair. Play safe." />
        <div className="grid gap-3 sm:grid-cols-2">
          {rules.map((r, i) => (
            <div key={i} className="glass flex gap-3 rounded-lg px-4 py-3">
              <span className="font-mono text-xs font-bold text-neon">{String(i + 1).padStart(2, '0')}</span>
              <span className="text-sm leading-relaxed text-slate-300">{r}</span>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <div className="glass neon-border relative overflow-hidden rounded-2xl px-6 py-12 text-center">
          <div className="font-mono text-xs uppercase tracking-[.3em] text-cyan">// your move</div>
          <h2 className="mt-3 font-display text-3xl font-bold text-white md:text-5xl">Ready to breach the target?</h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-400">
            Form your team of 2–4, get approved, enter the lobby and wait for the organiser to open Round 1.
          </p>
          <div className="mt-7 flex justify-center gap-3">
            <Link to="/register" className="btn btn-primary">REGISTER NOW</Link>
            <Link to="/login" className="btn btn-ghost">ALREADY REGISTERED?</Link>
          </div>
        </div>
      </section>

      {/* ORGANISERS */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <SectionTitle kicker="organised by" title="Two chapters. One mission." align="center" />
        <div className="mx-auto flex max-w-3xl flex-col gap-4 sm:flex-row sm:justify-center">
          <div className="glass neon-border flex-1 rounded-xl p-6 text-center">
            <div className="mx-auto w-fit"><OrganiserMark kind="pragyan" /></div>
            <p className="mt-4 text-sm text-slate-400">Pragyan — the techno-cultural celebration of innovation.</p>
          </div>
          <div className="glass cyan-border flex-1 rounded-xl p-6 text-center">
            <div className="mx-auto w-fit"><OrganiserMark kind="ieee" /></div>
            <p className="mt-4 text-sm text-slate-400">IEEE Computer Society, KLEIT Chapter — advancing computing education.</p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-4xl px-5 py-16">
        <SectionTitle kicker="intel" title="Frequently asked questions" align="center" />
        <div className="space-y-3">
          {faqs.map(([q, a]) => (
            <details key={q} className="glass group rounded-lg px-5 py-4">
              <summary className="cursor-pointer font-display text-sm font-semibold text-white">{q}</summary>
              <p className="mt-3 text-sm leading-relaxed text-slate-400">{a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CONTACT */}
      <section className="mx-auto max-w-7xl px-5 py-16">
        <div className="glass violet-border rounded-xl p-8 text-center">
          <div className="font-mono text-xs uppercase tracking-[.3em] text-violet">// comms channel</div>
          <h2 className="mt-3 font-display text-2xl font-bold text-white">Need help during the event?</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-slate-400">
            Announcements appear on your team dashboard in real time. Organisers can be reached through
            the event help desk announced during the opening ceremony.
          </p>
        </div>
      </section>
    </>
  )
}
