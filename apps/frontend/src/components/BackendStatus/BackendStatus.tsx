import { useEffect, useState } from 'react'
import styles from './BackendStatus.module.css'

interface StatusData {
  state: 'starting' | 'loading' | 'ready' | 'error'
  message?: string
  progress?: number
}

export default function BackendStatus() {
  const [status, setStatus] = useState<StatusData | null>(
    window.electronAPI ? { state: 'starting', message: 'Starting backend...' } : null
  )

  useEffect(() => {
    if (!window.electronAPI?.onBackendStatus) return
    window.electronAPI.onBackendStatus(setStatus)
  }, [])

  if (!status || status.state === 'ready') return null

  const isError = status.state === 'error'
  const color = isError ? '#ef4444' : '#2563eb'
  const progressPct = status.progress != null ? Math.round(status.progress * 100) : 0

  return (
    <div className={styles.bar} style={{ backgroundColor: color }}>
      <div className={styles.content}>
        <span className={styles.dot} />
        <span className={styles.text}>{status.message || status.state}</span>
      </div>
      {!isError && progressPct > 0 && (
        <div className={styles.progressTrack}>
          <div
            className={styles.progressFill}
            style={{ width: `${Math.min(progressPct, 100)}%` }}
          />
        </div>
      )}
    </div>
  )
}
