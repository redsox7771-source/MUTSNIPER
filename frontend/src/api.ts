import type { BuyResult, CardMarket, ListCardResult, OwnedCard, Snipe } from './types'

export async function fetchSnipes(params: { minMarginPct?: number; minOvr?: number } = {}): Promise<Snipe[]> {
  const search = new URLSearchParams()
  if (params.minMarginPct) search.set('min_margin_pct', String(params.minMarginPct))
  if (params.minOvr) search.set('min_ovr', String(params.minOvr))
  const res = await fetch(`/api/snipes?${search.toString()}`)
  if (!res.ok) throw new Error(`Failed to load snipes: ${res.status}`)
  return res.json()
}

export async function buySnipe(listingId: string): Promise<BuyResult> {
  const res = await fetch(`/api/snipes/${listingId}/buy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirm: true }),
  })
  if (!res.ok) throw new Error(`Buy failed: ${res.status}`)
  return res.json()
}

export async function fetchBinder(): Promise<OwnedCard[]> {
  const res = await fetch('/api/binder')
  if (!res.ok) throw new Error(`Failed to load binder: ${res.status}`)
  return res.json()
}

export async function listCard(
  cardId: string,
  body: { buyNowPrice: number; startBid: number; durationSeconds: number },
): Promise<ListCardResult> {
  const res = await fetch(`/api/binder/${cardId}/list`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      buy_now_price: body.buyNowPrice,
      start_bid: body.startBid,
      duration_seconds: body.durationSeconds,
      confirm: true,
    }),
  })
  if (!res.ok) throw new Error(`List failed: ${res.status}`)
  return res.json()
}

export async function fetchCardMarket(cardId: string): Promise<CardMarket> {
  const res = await fetch(`/api/cards/${cardId}/market`)
  if (!res.ok) throw new Error(`Failed to load card market: ${res.status}`)
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
