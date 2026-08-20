import type { Snipe } from '../types'

function timeRemaining(expiresAt: string): string {
  const ms = new Date(expiresAt).getTime() - Date.now()
  if (ms <= 0) return 'Ended'
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatCoins(n: number): string {
  return n.toLocaleString('en-US')
}

interface Props {
  snipe: Snipe
  pinned: boolean
  onTogglePin: () => void
}

export function SnipeRow({ snipe, pinned, onTogglePin }: Props) {
  const coinProfit = snipe.est_value - snipe.buy_now

  return (
    <tr className={pinned ? 'row-pinned' : undefined}>
      <td className="col-card">
        <span className="card-name">{snipe.card_name}</span>
        <span className="card-meta">
          {snipe.program} · {snipe.position}
        </span>
      </td>
      <td className="col-ovr">{snipe.ovr}</td>
      <td className="col-price">{formatCoins(snipe.buy_now)}</td>
      <td className="col-price">{formatCoins(Math.round(snipe.est_value))}</td>
      <td className="col-margin">
        <span className="margin-pct">{(snipe.margin_pct * 100).toFixed(0)}%</span>
        <span className="margin-coins">+{formatCoins(Math.round(coinProfit))}</span>
      </td>
      <td className="col-time">{timeRemaining(snipe.expires_at)}</td>
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
