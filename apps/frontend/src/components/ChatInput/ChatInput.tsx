import { useRef, useCallback, useEffect, useState } from 'react'
import { ArrowUp } from 'lucide-react'
import VoiceButton from '../VoiceButton/VoiceButton'
import VoiceLevelIndicator from '../VoiceLevelIndicator/VoiceLevelIndicator'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import styles from './ChatInput.module.css'

interface ChatInputProps {
  onSend: (text: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [voiceTranscript, setVoiceTranscript] = useState('')

  const handleFinalTranscript = useCallback((text: string) => {
    setVoiceTranscript(text)
    onSend(text)
  }, [onSend])

  const {
    isSupported,
    isListening,
    error: speechError,
    audioLevel,
    startListening,
    stopListening,
  } = useSpeechRecognition(handleFinalTranscript)

  const handleVoiceToggle = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  const handleSend = useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea || isLoading) return
    const text = textarea.value.trim()
    if (!text) return
    onSend(text)
    textarea.value = ''
    textarea.style.height = 'auto'
  }, [onSend, isLoading])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }, [handleSend])

  const handleInput = useCallback(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
  }, [])

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  return (
    <div className={styles.inputArea}>
      {speechError && (
        <div className={styles.errorBar}>
          <span>{speechError}</span>
        </div>
      )}
      {isListening && !speechError && (
        <div className={styles.listeningBar}>
          <span className={styles.listeningDot} />
          <span className={styles.listeningLabel}>
            {voiceTranscript || 'Listening...'}
          </span>
          <VoiceLevelIndicator level={audioLevel} />
        </div>
      )}
      <div className={styles.inputContainer}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Type a message..."
          rows={1}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={isLoading || isListening}
        />
        <VoiceButton
          isListening={isListening}
          isSupported={isSupported}
          isLoading={isLoading}
          onClick={handleVoiceToggle}
        />
        <button
          className={styles.sendBtn}
          onClick={handleSend}
          disabled={isLoading || isListening}
          title="Send (Enter)"
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  )
}
