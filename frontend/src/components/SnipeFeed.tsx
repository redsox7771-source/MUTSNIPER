import type { Snipe } from '../types'
import { SnipeRow } from './SnipeRow'

export function SnipeFeed({ snipes }: { snipes: Snipe[] }) {
  if (snipes.length === 0) {
    return <div className="empty-state">No snipes yet — watching the market.</div>
  }
  return (
    <table className="snipe-table">
      <thead>
        <tr>
          <th>Card</th>
          <th>OVR</th>
          <th>Buy now</th>
          <th>Est. value</th>
          <th>Margin</th>
          <th>Time left</th>
        </tr>
      </thead>
      <tbody>
        {snipes.map((s) => (
          <SnipeRow key={s.listing_id} snipe={s} />
        ))}
      </tbody>
    </table>
  )
}
