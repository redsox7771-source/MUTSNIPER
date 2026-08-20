import { useEffect, useMemo, useRef, useState } from 'react'
import type { Snipe } from './types'
import { fetchSnipes, connectFeed, buySnipe, type ConnectionStatus as Status } from './api'
import { SnipeFeed, type SortKey, type SortDir } from './components/SnipeFeed'
import { FilterBar } from './components/FilterBar'
import { ConnectionStatus } from './components/ConnectionStatus'
import { BinderView } from './components/BinderView'

const PINNED_STORAGE_KEY = 'mutsniper.pinnedListingIds'

function loadPinned(): Set<string> {
  try {
    const raw = localStorage.getItem(PINNED_STORAGE_KEY)
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

export default function App() {
  const [view, setView] = useState<'feed' | 'binder'>('feed')
  const [snipes, setSnipes] = useState<Snipe[]>([])
  const [status, setStatus] = useState<Status>('disconnected')
  const [paused, setPaused] = useState(false)
  const [minMarginPct, setMinMarginPct] = useState(0)
  const [minOvr, setMinOvr] = useState(0)
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(() => loadPinned())
  const [sortKey, setSortKey] = useState<SortKey>('detected_at')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
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

  useEffect(() => {
    localStorage.setItem(PINNED_STORAGE_KEY, JSON.stringify([...pinnedIds]))
  }, [pinnedIds])

  const togglePinned = (listingId: string) => {
    setPinnedIds((prev) => {
      const next = new Set(prev)
      if (next.has(listingId)) next.delete(listingId)
      else next.add(listingId)
      return next
    })
  }

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'time_left' ? 'asc' : 'desc')
    }
  }

  const handleBuy = async (listingId: string): Promise<boolean> => {
    const result = await buySnipe(listingId)
    if (result.success) {
      setSnipes((prev) => prev.filter((s) => s.listing_id !== listingId))
      setPinnedIds((prev) => {
        if (!prev.has(listingId)) return prev
        const next = new Set(prev)
        next.delete(listingId)
        return next
      })
    }
    return result.success
  }

  const visible = useMemo(
    () => snipes.filter((s) => s.margin_pct >= minMarginPct && s.ovr >= minOvr),
    [snipes, minMarginPct, minOvr],
  )

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1>mutsniper</h1>
          <nav className="view-tabs">
            <button className={view === 'feed' ? 'view-tab view-tab--active' : 'view-tab'} onClick={() => setView('feed')}>
              Feed
            </button>
            <button className={view === 'binder' ? 'view-tab view-tab--active' : 'view-tab'} onClick={() => setView('binder')}>
              Binder
            </button>
          </nav>
        </div>
        <ConnectionStatus status={status} paused={paused} onTogglePause={() => setPaused((p) => !p)} />
      </header>

      {view === 'feed' ? (
        <>
          <FilterBar
            minMarginPct={minMarginPct}
            minOvr={minOvr}
            onChange={(next) => {
              setMinMarginPct(next.minMarginPct)
              setMinOvr(next.minOvr)
            }}
          />
          <SnipeFeed
            snipes={visible}
            pinnedIds={pinnedIds}
            onTogglePin={togglePinned}
            onBuy={handleBuy}
            sortKey={sortKey}
            sortDir={sortDir}
            onSort={handleSort}
          />
        </>
      ) : (
        <BinderView />
      )}
    </div>
  )
}
