import { useMicrophones } from '../../hooks/useMicrophones'
import styles from './MicrophoneSelector.module.css'

export default function MicrophoneSelector() {
  const { microphones, selected, loading, error, select, refresh } = useMicrophones()

  return (
    <div className={styles.container}>
      <label className={styles.label}>Input Device</label>

      <div className={styles.controlRow}>
        <select
          className={styles.select}
          value={selected?.id ?? ''}
          disabled={loading || microphones.length === 0}
          onChange={e => select(e.target.value)}
        >
          {loading && <option value="">Loading...</option>}
          {!loading &&
            microphones.map(mic => (
              <option key={mic.id} value={mic.id}>
                {mic.name}{mic.default ? ' (Default)' : ''}
              </option>
            ))}
        </select>

        <button
          className={styles.refreshBtn}
          onClick={refresh}
          disabled={loading}
          title="Refresh devices"
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
          {selected.id !== 'default' && (
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>ID:</span>
              <span className={styles.infoValue} title={selected.id}>
                {selected.id.length > 24
                  ? selected.id.slice(0, 24) + '...'
                  : selected.id}
              </span>
            </div>
          )}
        </div>
      )}

      {loading && <div className={styles.hint}>Scanning for microphones...</div>}

      {microphones.length === 0 && !loading && (
        <div className={styles.hint}>No microphones found. Check your microphone connection.</div>
      )}

      {error && <div className={styles.error}>{error}</div>}
    </div>
  )
}
