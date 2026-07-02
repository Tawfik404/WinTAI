import { useEffect, useState } from 'react'
import styles from './BackendStatus.module.css'

interface StatusData {
  state: 'starting' | 'ready' | 'error'
  message?: string
}

declare global {
  interface Window {
    electronAPI?: {
      platform: string
      onBackendStatus: (callback: (status: StatusData) => void) => void
    }
  }
}

export default function BackendStatus() {
  const [status, setStatus] = useState<StatusData | null>(
    window.electronAPI ? { state: 'starting', message: 'Starting backend...' } : null
  )

  useEffect(() => {
    if (!window.electronAPI) return
    window.electronAPI.onBackendStatus(setStatus)
  }, [])

  if (!status || status.state === 'ready') return null

  const color = status.state === 'starting' ? '#f59e0b' : '#ef4444'

  return (
    <div className={styles.bar} style={{ backgroundColor: color }}>
      <span className={styles.dot} />
      <span className={styles.text}>{status.message || status.state}</span>
    </div>
  )
}
