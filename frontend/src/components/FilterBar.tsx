interface Props {
  minMarginPct: number
  minOvr: number
  onChange: (next: { minMarginPct: number; minOvr: number }) => void
}

export function FilterBar({ minMarginPct, minOvr, onChange }: Props) {
  return (
    <div className="filter-bar">
      <label>
        Min margin
        <select
          value={minMarginPct}
          onChange={(e) => onChange({ minMarginPct: Number(e.target.value), minOvr })}
        >
          <option value={0}>Any</option>
          <option value={0.25}>25%+</option>
          <option value={0.4}>40%+</option>
          <option value={0.6}>60%+</option>
        </select>
      </label>
      <label>
        Min OVR
        <select
          value={minOvr}
          onChange={(e) => onChange({ minMarginPct, minOvr: Number(e.target.value) })}
        >
          <option value={0}>Any</option>
          <option value={85}>85+</option>
          <option value={90}>90+</option>
          <option value={95}>95+</option>
        </select>
      </label>
    </div>
  )
}
