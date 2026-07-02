import { X } from 'lucide-react'
import styles from './Settings.module.css'

interface SettingsProps {
  open: boolean
  onClose: () => void
}

export default function Settings({ open, onClose }: SettingsProps) {
  if (!open) return null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.panel} onClick={e => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Settings</h2>
          <button className={styles.closeBtn} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>Connection</div>
          <div className={styles.sectionContent}>
            Backend URL: <code>http://127.0.0.1:8000</code>
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>About</div>
          <div className={styles.sectionContent}>
            WinTAI — Windows AI Assistant<br />
            Version 0.1.0
          </div>
        </div>

        <div className={styles.section}>
          <div className={styles.sectionTitle}>Keyboard Shortcuts</div>
          <div className={styles.sectionContent}>
            <code>Enter</code> Send message<br />
            <code>Shift+Enter</code> New line
          </div>
        </div>
      </div>
    </div>
  )
}
