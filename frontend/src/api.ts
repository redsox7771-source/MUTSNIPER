import type { Snipe } from './types'

export async function fetchSnipes(params: { minMarginPct?: number; minOvr?: number } = {}): Promise<Snipe[]> {
  const search = new URLSearchParams()
  if (params.minMarginPct) search.set('min_margin_pct', String(params.minMarginPct))
  if (params.minOvr) search.set('min_ovr', String(params.minOvr))
  const res = await fetch(`/api/snipes?${search.toString()}`)
  if (!res.ok) throw new Error(`Failed to load snipes: ${res.status}`)
  return res.json()
}

export type ConnectionStatus = 'connected' | 'disconnected'

export function connectFeed(
  onSnipe: (snipe: Snipe) => void,
  onStatusChange: (status: ConnectionStatus) => void,
): () => void {
  let socket: WebSocket | null = null
  let closedByCaller = false
  let retryDelay = 1000

  function open() {
    socket = new WebSocket(`${location.origin.replace(/^http/, 'ws')}/ws/feed`)
    socket.onopen = () => {
      retryDelay = 1000
      onStatusChange('connected')
    }
    socket.onmessage = (event) => {
      onSnipe(JSON.parse(event.data))
    }
    socket.onclose = () => {
      onStatusChange('disconnected')
      if (!closedByCaller) {
        setTimeout(open, retryDelay)
        retryDelay = Math.min(retryDelay * 2, 30000)
      }
    }
    socket.onerror = () => socket?.close()
  }

  open()

  return () => {
    closedByCaller = true
    socket?.close()
  }
}
