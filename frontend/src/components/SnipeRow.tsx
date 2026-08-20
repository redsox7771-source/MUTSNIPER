import { useState } from 'react'
import type { Snipe } from '../types'
import { formatCoins, ovrBadgeClass, timeRemaining } from '../format'

interface Props {
  snipe: Snipe
  pinned: boolean
  onTogglePin: () => void
  onBuy: (listingId: string) => Promise<boolean>
}

export function SnipeRow({ snipe, pinned, onTogglePin, onBuy }: Props) {
  const [buying, setBuying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const coinProfit = snipe.est_value - snipe.buy_now

  const handleBuy = async () => {
    const ok = window.confirm(
      `Buy ${snipe.card_name} (${snipe.ovr} OVR) now for ${formatCoins(snipe.buy_now)} coins?`,
    )
    if (!ok) return

    setBuying(true)
    setError(null)
    try {
      const success = await onBuy(snipe.listing_id)
      if (!success) setError('Purchase failed')
    } catch {
      setError('Purchase failed')
    } finally {
      setBuying(false)
    }
  }

  return (
    <tr className={pinned ? 'row-pinned' : undefined}>
      <td className="col-card">
        <span className="card-name">{snipe.card_name}</span>
        <span className="card-meta">
          {snipe.program} · {snipe.position}
        </span>
      </td>
      <td className="col-ovr">
        <span className={ovrBadgeClass(snipe.ovr)}>{snipe.ovr}</span>
      </td>
      <td className="col-price">{formatCoins(snipe.buy_now)}</td>
      <td className="col-price">{formatCoins(Math.round(snipe.est_value))}</td>
      <td className="col-margin">
        <span className="margin-pct">{(snipe.margin_pct * 100).toFixed(0)}%</span>
        <span className="margin-coins">+{formatCoins(Math.round(coinProfit))}</span>
      </td>
      <td className="col-time">{timeRemaining(snipe.expires_at)}</td>
      <td className="col-buy">
        <button className="buy-btn" onClick={handleBuy} disabled={buying}>
          {buying ? 'Buying…' : 'Buy'}
        </button>
        {error && <span className="row-error">{error}</span>}
      </td>
      <td className="col-pin">
        <button
          className={`pin-btn${pinned ? ' pin-btn--active' : ''}`}
          onClick={onTogglePin}
          aria-label={pinned ? 'Unpin' : 'Pin'}
          title={pinned ? 'Unpin' : 'Pin to top'}
        >
          {pinned ? '★' : '☆'}
        </button>
      </td>
    </tr>
  )
}
