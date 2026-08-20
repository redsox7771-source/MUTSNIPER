export interface Snipe {
  listing_id: string
  card_id: string
  card_name: string
  ovr: number
  program: string
  position: string
  buy_now: number
  est_value: number
  margin: number
  margin_pct: number
  expires_at: string
  detected_at: string
}

export interface OwnedCard {
  card_id: string
  card_name: string
  ovr: number
  program: string
  position: string
  team: string
  quantity: number
  tradeable: boolean
}

export interface BuyResult {
  listing_id: string
  success: boolean
  price_paid: number
  message: string
}

export interface ListCardResult {
  card_id: string
  success: boolean
  listing_id: string | null
  message: string
}
