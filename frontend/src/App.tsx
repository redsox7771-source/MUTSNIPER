import { useEffect, useMemo, useRef, useState } from 'react'
import type { Snipe } from './types'
import { fetchSnipes, connectFeed, type ConnectionStatus as Status } from './api'
import { SnipeFeed } from './components/SnipeFeed'
import { FilterBar } from './components/FilterBar'
import { ConnectionStatus } from './components/ConnectionStatus'

export default function App() {
  const [snipes, setSnipes] = useState<Snipe[]>([])
  const [status, setStatus] = useState<Status>('disconnected')
  const [paused, setPaused] = useState(false)
  const [minMarginPct, setMinMarginPct] = useState(0)
  const [minOvr, setMinOvr] = useState(0)
  const pausedRef = useRef(paused)
  pausedRef.current = paused

  useEffect(() => {
    fetchSnipes({ minMarginPct, minOvr }).then(setSnipes).catch(() => {})
  }, [minMarginPct, minOvr])

  useEffect(() => {
    const close = connectFeed((snipe) => {
      if (pausedRef.current) return
      setSnipes((prev) => {
        if (prev.some((s) => s.listing_id === snipe.listing_id)) return prev
        return [snipe, ...prev].slice(0, 200)
      })
    }, setStatus)
    return close
  }, [])

  const visible = useMemo(
    () => snipes.filter((s) => s.margin_pct >= minMarginPct && s.ovr >= minOvr),
    [snipes, minMarginPct, minOvr],
  )

  return (
    <div className="app">
      <header className="app-header">
        <h1>mutsniper</h1>
        <ConnectionStatus status={status} paused={paused} onTogglePause={() => setPaused((p) => !p)} />
      </header>
      <FilterBar
        minMarginPct={minMarginPct}
        minOvr={minOvr}
        onChange={(next) => {
          setMinMarginPct(next.minMarginPct)
          setMinOvr(next.minOvr)
        }}
      />
      <SnipeFeed snipes={visible} />
    </div>
  )
}
