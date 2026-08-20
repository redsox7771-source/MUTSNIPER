export function formatCoins(n: number): string {
  return n.toLocaleString('en-US')
}

export function timeRemaining(expiresAt: string): string {
  const ms = new Date(expiresAt).getTime() - Date.now()
  if (ms <= 0) return 'Ended'
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

// mut.gg's individual card pages are /players/{their-internal-id}-{slug}/ -
// that internal id isn't something our card data has, so we can't link
// straight to one reliably. Their list page at /players/ is real and
// always valid though, so we land there with a best-effort search param:
// if it filters, great; if the param name is wrong, it just shows the
// unfiltered list - either way it's a genuine mut.gg page, never a 404.
export function cardSearchUrl(cardName: string): string {
  return `https://www.mut.gg/players/?search=${encodeURIComponent(cardName)}`
}

export function ovrBadgeClass(ovr: number): string {
  if (ovr >= 99) return 'ovr-badge ovr-badge--elite'
  if (ovr >= 95) return 'ovr-badge ovr-badge--great'
  return 'ovr-badge'
}

export function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime()
  if (ms < 60_000) return 'just now'
  const totalMinutes = Math.floor(ms / 60_000)
  if (totalMinutes < 60) return `${totalMinutes}m ago`
  const hours = Math.floor(totalMinutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
