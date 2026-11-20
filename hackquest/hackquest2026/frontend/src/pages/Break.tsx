import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, errorText } from '../lib/api'
import { Badge, Countdown, Marquee } from '../components/Ui'

export default function BreakPage() {
  const { number = '1' } = useParams()
  const [data, setData] = useState<any>(null)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState('')
  const [revealed, setRevealed] = useState<string | null>(null)
  const [seconds, setSeconds] = useState(90)

  useEffect(() => {
    api.get('/api/public/break/' + number).then(setData).catch(() => {})
  }, [number])
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s > 0 ? s - 1 : 0), 1000)
    return () => clearInterval(id)
  }, [])

  function check(e: React.FormEvent) {
    e.preventDefault()
    if (!answer.trim()) return
    setFeedback('Answer recorded for the break room. The organiser controls the official reveal.')
  }

  async function reveal() {
    try {
      const res = await api.get<any>('/api/public/reveal/' + data.riddle.id)
      setRevealed(res.answer)
    } catch (e) { setFeedback(errorText(e)) }
  }

  const riddle = data?.riddle
  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <div className="mb-8 text-center">
        <div className="font-mono text-xs uppercase tracking-[.3em] text-violet">// scheduled break {number}</div>
        <h1 className="mt-2 font-display text-3xl font-bold text-white md:text-4xl">Cyber riddle & meme break</h1>
        <p className="mt-2 text-sm text-slate-400">Stretch your brain, not the rules. Riddles carry no official points.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="glass violet-border rounded-xl p-6">
          <div className="flex items-center justify-between">
            <Badge tone="violet">{riddle?.category || 'RIDDLE'}</Badge>
            <span className="font-mono text-lg font-bold text-violet">
              {String(Math.floor(seconds / 60)).padStart(2, '0')}:{String(seconds % 60).padStart(2, '0')}
            </span>
          </div>
          <p className="mt-6 font-display text-lg leading-relaxed text-white">
            {riddle?.question || 'Loading riddle…'}
          </p>
          <p className="mt-4 text-sm text-slate-400">Hint: {riddle?.hint}</p>
          <form onSubmit={check} className="mt-6">
            <input className="input" placeholder="Your answer (unscored)" value={answer}
                   onChange={(e) => setAnswer(e.target.value)} />
            <button className="btn btn-ghost mt-3 w-full">CHECK ANSWER</button>
          </form>
          {feedback && <p className="mt-3 font-mono text-xs text-cyan">{feedback}</p>}
          {riddle?.reveal_enabled && (
            <button onClick={reveal} className="btn btn-ghost mt-3 w-full">REVEAL ANSWER</button>
          )}
          {revealed && <p className="mt-3 font-mono text-sm text-neon">ANSWER: {revealed}</p>}
        </div>

        <div className="glass cyan-border flex flex-col justify-between rounded-xl p-6">
          <div>
            <Badge tone="cyan">MEME DROP</Badge>
            <h2 className="mt-6 font-display text-2xl font-bold text-white">{data?.meme?.title || 'Loading…'}</h2>
            <p className="mt-4 font-mono text-sm leading-relaxed text-cyan">
              {data?.meme?.caption}
            </p>
          </div>
          <div className="mt-8 rounded-lg border border-dashed border-slate-700 p-6 text-center font-mono text-xs text-slate-500">
            [ original text-based meme template · organiser-editable ]
          </div>
        </div>
      </div>

      <div className="mt-10 text-center">
        <Link to="/dashboard" className="btn btn-primary">BACK TO ARENA</Link>
      </div>
      <div className="mt-10"><Marquee text="DECODE • DEBUG • DETECT • DOMINATE • CAPTURE THE FLAG • " /></div>
      <div className="mt-6 text-center"><Countdown target="2026-11-25T11:00:00+05:30" /></div>
    </div>
  )
}
