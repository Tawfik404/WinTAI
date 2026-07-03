import { Mic, MicOff, Loader2 } from 'lucide-react'
import styles from './VoiceButton.module.css'

interface VoiceButtonProps {
  isListening: boolean
  isSupported: boolean
  isLoading: boolean
  onClick: () => void
}

export default function VoiceButton({
  isListening,
  isSupported,
  isLoading,
  onClick,
}: VoiceButtonProps) {
  if (!isSupported) return null

  const handleClick = () => {
    if (!isLoading) onClick()
  }

  const btnClass = [
    styles.voiceBtn,
    isListening ? styles.listening : '',
  ].join(' ')

  return (
    <button
      className={btnClass}
      onClick={handleClick}
      disabled={isLoading}
      title={isListening ? 'Stop listening' : 'Start voice input'}
    >
      {isLoading ? (
        <Loader2 size={18} className={styles.spinner} />
      ) : isListening ? (
        <Mic size={18} />
      ) : (
        <MicOff size={18} />
      )}
    </button>
  )
}
