import { useEffect, useState } from 'react'
import type { CardMarket, OwnedCard } from '../types'
import { fetchBinder, fetchCardMarket, listCard } from '../api'
import { formatCoins, ovrBadgeClass, timeAgo, timeRemaining } from '../format'

function CardMarketPanel({ cardId }: { cardId: string }) {
  const [market, setMarket] = useState<CardMarket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetchCardMarket(cardId)
      .then(setMarket)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [cardId])

  if (loading) return <div className="market-panel-empty">Loading market…</div>
  if (error || !market) return <div className="market-panel-empty">Couldn't load market data.</div>

  return (
    <div className="market-panel">
      <div className="market-col">
        <h4>Recently sold</h4>
        {market.recent_sales.length === 0 ? (
          <div className="market-panel-empty">No recent sales seen.</div>
        ) : (
          <ul className="market-list">
            {market.recent_sales.map((sale) => (
              <li key={sale.listing_id}>
                <span>{formatCoins(sale.price)}</span>
                <span className="market-list-meta">{timeAgo(sale.sold_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="market-col">
        <h4>Currently listed</h4>
        {market.active_listings.length === 0 ? (
          <div className="market-panel-empty">Nothing currently listed.</div>
        ) : (
          <ul className="market-list">
            {market.active_listings.map((listing) => (
              <li key={listing.listing_id}>
                <span>{formatCoins(listing.buy_now || listing.current_bid)}</span>
                <span className="market-list-meta">{timeRemaining(listing.expires_at)} left</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function BinderRow({ card, onListed }: { card: OwnedCard; onListed: () => void }) {
  const [startBid, setStartBid] = useState('')
  const [buyNow, setBuyNow] = useState('')
  const [listing, setListing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  const handleList = async () => {
    const startBidPrice = Number(startBid)
    const buyNowPrice = Number(buyNow)

    if (!startBidPrice || startBidPrice <= 0 || !buyNowPrice || buyNowPrice <= 0) {
      setMessage('Enter both prices')
      return
    }
    if (startBidPrice > buyNowPrice) {
      setMessage('Start bid must be ≤ buy now')
      return
    }

    const ok = window.confirm(
      `List ${card.card_name}: start bid ${formatCoins(startBidPrice)}, buy now ${formatCoins(buyNowPrice)}?`,
    )
    if (!ok) return

    setListing(true)
    setMessage(null)
    try {
      const result = await listCard(card.card_id, {
        buyNowPrice,
        startBid: startBidPrice,
        durationSeconds: 3600,
      })
      if (result.success) {
        setStartBid('')
        setBuyNow('')
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
    <>
      <tr className={expanded ? 'row-expanded' : undefined}>
        <td className="col-card">
          <button className="card-name-btn" onClick={() => setExpanded((e) => !e)}>
            <span className="card-name">{card.card_name}</span>
            <span className="card-meta">
              {card.program} · {card.position}
            </span>
          </button>
        </td>
        <td className="col-ovr">
          <span className={ovrBadgeClass(card.ovr)}>{card.ovr}</span>
        </td>
        <td className="col-price">{card.quantity}</td>
        <td className="col-list-price">
          <input
            type="number"
            className="list-price-input"
            placeholder="Start bid"
            value={startBid}
            onChange={(e) => setStartBid(e.target.value)}
            disabled={!card.tradeable || listing}
          />
        </td>
        <td className="col-list-price">
          <input
            type="number"
            className="list-price-input"
            placeholder="Buy now"
            value={buyNow}
            onChange={(e) => setBuyNow(e.target.value)}
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
      {expanded && (
        <tr className="market-panel-row">
          <td colSpan={6}>
            <CardMarketPanel cardId={card.card_id} />
          </td>
        </tr>
      )}
    </>
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
          <th className="col-list-price">Start bid</th>
          <th className="col-list-price">Buy now</th>
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
