import { useMemo } from 'react'
import styles from './VoiceLevelIndicator.module.css'

interface VoiceLevelIndicatorProps {
  level: number
  barCount?: number
}

export default function VoiceLevelIndicator({
  level,
  barCount = 20,
}: VoiceLevelIndicatorProps) {
  const bars = useMemo(() => {
    const result: number[] = []
    for (let i = 0; i < barCount; i++) {
      const pos = (i + 0.5) / barCount
      const barHeight = Math.max(0.02, level * Math.max(0.1, 1 - Math.abs(pos - 0.5) * 1.4))
      result.push(Math.min(1, barHeight))
    }
    return result
  }, [level, barCount])

  return (
    <div className={styles.container}>
      {bars.map((h, i) => (
        <div
          key={i}
          className={styles.bar}
          style={{ height: `${Math.max(2, h * 48)}px` }}
        />
      ))}
    </div>
  )
}
