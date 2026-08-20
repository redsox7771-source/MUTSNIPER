import { useEffect, useState } from 'react'
import type { OwnedCard } from '../types'
import { fetchBinder, listCard } from '../api'

function formatCoins(n: number): string {
  return n.toLocaleString('en-US')
}

function BinderRow({ card, onListed }: { card: OwnedCard; onListed: () => void }) {
  const [price, setPrice] = useState('')
  const [listing, setListing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const handleList = async () => {
    const buyNowPrice = Number(price)
    if (!buyNowPrice || buyNowPrice <= 0) {
      setMessage('Enter a price')
      return
    }
    const ok = window.confirm(`List ${card.card_name} for ${formatCoins(buyNowPrice)} coins buy-now?`)
    if (!ok) return

    setListing(true)
    setMessage(null)
    try {
      const result = await listCard(card.card_id, {
        buyNowPrice,
        startBid: Math.round(buyNowPrice * 0.5),
        durationSeconds: 3600,
      })
      if (result.success) {
        setPrice('')
        onListed()
      } else {
        setMessage(result.message)
      }
    } catch {
      setMessage('List failed')
    } finally {
      setListing(false)
    }
  }

  return (
    <tr>
      <td className="col-card">
        <span className="card-name">{card.card_name}</span>
        <span className="card-meta">
          {card.program} · {card.position}
        </span>
      </td>
      <td className="col-ovr">{card.ovr}</td>
      <td className="col-price">{card.quantity}</td>
      <td className="col-list-price">
        <input
          type="number"
          className="list-price-input"
          placeholder="Buy now price"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          disabled={!card.tradeable || listing}
        />
      </td>
      <td className="col-buy">
        <button className="buy-btn" onClick={handleList} disabled={!card.tradeable || listing}>
          {listing ? 'Listing…' : 'List'}
        </button>
        {message && <span className="row-error">{message}</span>}
      </td>
    </tr>
  )
}

export function BinderView() {
  const [cards, setCards] = useState<OwnedCard[]>([])
  const [loading, setLoading] = useState(true)

  const reload = () => {
    setLoading(true)
    fetchBinder()
      .then(setCards)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(reload, [])

  if (loading) {
    return <div className="empty-state">Loading binder…</div>
  }
  if (cards.length === 0) {
    return <div className="empty-state">No tradeable cards in your binder.</div>
  }

  return (
    <table className="snipe-table">
      <thead>
        <tr>
          <th className="col-card">Card</th>
          <th className="col-ovr">OVR</th>
          <th className="col-price">Qty</th>
          <th className="col-list-price">List price</th>
          <th className="col-buy" />
        </tr>
      </thead>
      <tbody>
        {cards.map((card) => (
          <BinderRow key={card.card_id} card={card} onListed={reload} />
        ))}
      </tbody>
    </table>
  )
}
