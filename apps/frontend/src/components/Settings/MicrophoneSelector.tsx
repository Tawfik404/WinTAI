import { useState, useRef, useEffect } from 'react'
import { useMicrophones } from '../../hooks/useMicrophones'
import styles from './MicrophoneSelector.module.css'

const BAR_COUNT = 5

function LevelBars({ level }: { level: number }) {
  const filled = Math.round(level * BAR_COUNT)

  return (
    <span className={styles.levelBars}>
      {Array.from({ length: BAR_COUNT }, (_, i) => (
        <span
          key={i}
          className={`${styles.levelBar} ${i < filled ? styles.levelBarOn : ''}`}
        />
      ))}
    </span>
  )
}

export default function MicrophoneSelector() {
  const { microphones, selected, loading, error, select, refresh, micLevels } = useMicrophones()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handle = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [open])

  return (
    <div className={styles.container} ref={rootRef}>
      <label className={styles.label}>Input Device</label>

      <div className={styles.controlRow}>
        <div className={styles.customSelect}>
          <button
            className={styles.selectBtn}
            onClick={() => !loading && setOpen(!open)}
            disabled={loading || microphones.length === 0}
            type="button"
          >
            <span className={styles.selectBtnText}>
              {loading ? 'Loading...' : selected?.name || 'Select microphone'}
            </span>
            <span className={styles.selectBtnArrow}>{open ? '▲' : '▼'}</span>
          </button>

          {open && (
            <div className={styles.optionsList}>
              {microphones.map(mic => {
                const level = micLevels[mic.id] ?? 0
                return (
                  <button
                    key={mic.id}
                    className={`${styles.option} ${selected?.id === mic.id ? styles.optionActive : ''}`}
                    onClick={() => { select(mic.id); setOpen(false) }}
                    type="button"
                  >
                    <LevelBars level={level} />
                    <span className={styles.optionName}>
                      {mic.name}
                      {mic.default ? <span className={styles.optionBadge}>Default</span> : ''}
                    </span>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <button
          className={styles.refreshBtn}
          onClick={refresh}
          disabled={loading}
          title="Refresh devices"
          type="button"
        >
          ↻
        </button>
      </div>

      {selected && (
        <div className={styles.info}>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Selected:</span>
            <span className={styles.infoValue}>{selected.name}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Status:</span>
            <span className={styles.statusOnline}>Connected</span>
          </div>
        </div>
      )}

      {loading && <div className={styles.hint}>Scanning microphones...</div>}

      {microphones.length === 0 && !loading && (
        <div className={styles.hint}>No microphones found. Check your microphone connection.</div>
      )}

      {error && <div className={styles.error}>{error}</div>}
    </div>
  )
}
