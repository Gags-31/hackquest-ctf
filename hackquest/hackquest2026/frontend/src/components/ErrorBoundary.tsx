import { Component, type ErrorInfo, type ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: Error | null }

/** Prevents a render error in any panel from leaving a blank screen. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Panel render error:', error, info.componentStack)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div className="mx-auto max-w-2xl px-5 py-16">
        <div className="glass rounded-xl border border-rose-500/50 p-6">
          <div className="font-mono text-xs uppercase tracking-[.3em] text-rose-400">// render error</div>
          <h1 className="mt-2 font-display text-xl font-bold text-white">This panel hit an error</h1>
          <p className="mt-2 font-mono text-sm text-slate-400">{this.state.error.message}</p>
          <button className="btn btn-primary mt-5" onClick={() => {
            this.setState({ error: null })
            window.location.reload()
          }}>
            RELOAD PANEL
          </button>
        </div>
      </div>
    )
  }
}
