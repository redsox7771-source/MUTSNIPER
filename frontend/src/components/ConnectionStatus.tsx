import type { ConnectionStatus as Status } from '../api'

interface Props {
  status: Status
  paused: boolean
  onTogglePause: () => void
}

export function ConnectionStatus({ status, paused, onTogglePause }: Props) {
  return (
    <div className="status-bar">
      <span className={`status-dot status-${status}`} />
      <span className="status-label">{status === 'connected' ? 'Live' : 'Reconnecting…'}</span>
      <button className="pause-btn" onClick={onTogglePause}>
        {paused ? 'Resume' : 'Pause'}
      </button>
    </div>
  )
}
