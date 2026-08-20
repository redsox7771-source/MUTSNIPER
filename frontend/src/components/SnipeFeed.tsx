import type { Snipe } from '../types'
import { SnipeRow } from './SnipeRow'

export type SortKey = 'detected_at' | 'card_name' | 'ovr' | 'buy_now' | 'est_value' | 'margin_pct' | 'time_left'
export type SortDir = 'asc' | 'desc'

interface Props {
  snipes: Snipe[]
  pinnedIds: Set<string>
  onTogglePin: (listingId: string) => void
  onBuy: (listingId: string) => Promise<boolean>
  sortKey: SortKey
  sortDir: SortDir
  onSort: (key: SortKey) => void
}

const SORT_VALUE: Record<SortKey, (s: Snipe) => number | string> = {
  detected_at: (s) => s.detected_at,
  card_name: (s) => s.card_name,
  ovr: (s) => s.ovr,
  buy_now: (s) => s.buy_now,
  est_value: (s) => s.est_value,
  margin_pct: (s) => s.margin_pct,
  time_left: (s) => s.expires_at,
}

function sortSnipes(snipes: Snipe[], key: SortKey, dir: SortDir): Snipe[] {
  const value = SORT_VALUE[key]
  const sign = dir === 'asc' ? 1 : -1
  return [...snipes].sort((a, b) => {
    const va = value(a)
    const vb = value(b)
    if (va < vb) return -1 * sign
    if (va > vb) return 1 * sign
    return 0
  })
}

const HEADERS: { key: SortKey; label: string; className: string }[] = [
  { key: 'card_name', label: 'Card', className: 'col-card' },
  { key: 'ovr', label: 'OVR', className: 'col-ovr' },
  { key: 'buy_now', label: 'Buy now', className: 'col-price' },
  { key: 'est_value', label: 'Est. value', className: 'col-price' },
  { key: 'margin_pct', label: 'Margin', className: 'col-margin' },
  { key: 'time_left', label: 'Time left', className: 'col-time' },
]

export function SnipeFeed({ snipes, pinnedIds, onTogglePin, onBuy, sortKey, sortDir, onSort }: Props) {
  if (snipes.length === 0) {
    return <div className="empty-state">No snipes yet — watching the market.</div>
  }

  // Pinned snipes always rank by raw coin profit (est_value - buy_now), not
  // the interactive sort - that's the whole point of pinning something.
  const pinned = snipes
    .filter((s) => pinnedIds.has(s.listing_id))
    .sort((a, b) => (b.est_value - b.buy_now) - (a.est_value - a.buy_now))

  const rest = sortSnipes(
    snipes.filter((s) => !pinnedIds.has(s.listing_id)),
    sortKey,
    sortDir,
  )

  return (
    <table className="snipe-table">
      <thead>
        <tr>
          {HEADERS.map((h) => (
            <th
              key={h.key}
              className={`${h.className} sortable`}
              onClick={() => onSort(h.key)}
            >
              {h.label}
              {sortKey === h.key && <span className="sort-arrow">{sortDir === 'asc' ? ' ▲' : ' ▼'}</span>}
            </th>
          ))}
          <th className="col-buy" />
          <th className="col-pin" />
        </tr>
      </thead>
      <tbody>
        {pinned.length > 0 && (
          <>
            <tr className="section-divider">
              <td colSpan={8}>Pinned · by coin profit</td>
            </tr>
            {pinned.map((s) => (
              <SnipeRow key={s.listing_id} snipe={s} pinned onTogglePin={() => onTogglePin(s.listing_id)} onBuy={onBuy} />
            ))}
            <tr className="section-divider">
              <td colSpan={8}>All snipes</td>
            </tr>
          </>
        )}
        {rest.map((s) => (
          <SnipeRow key={s.listing_id} snipe={s} pinned={false} onTogglePin={() => onTogglePin(s.listing_id)} onBuy={onBuy} />
        ))}
      </tbody>
    </table>
  )
}
