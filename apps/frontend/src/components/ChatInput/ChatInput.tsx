import { useRef, useCallback, useEffect } from 'react'
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

  // Duplicate-submission guard. A ref (not state) so it never triggers a re-render.
  const lastSubmittedRef = useRef<string>('')

  // ─── Single source of truth for sending ──────────────────────────────────
  // Both typed input (Enter / Send button) and automatic voice submission
  // go through this one function. An optional overrideText parameter lets
  // voice bypass the textarea DOM value while still clearing it afterward.
  const handleSend = useCallback((overrideText?: string) => {
    const textarea = textareaRef.current
    if (!textarea || isLoading) return

    const text = (overrideText !== undefined ? overrideText : textarea.value).trim()
    if (!text) return

    onSend(text)
    textarea.value = ''
    textarea.style.height = 'auto'
  }, [onSend, isLoading])

  // ─── Final transcript handler (voice → auto-submit) ───────────────────────
  const handleFinalTranscript = useCallback((text: string) => {
    const trimmed = text.trim()

    // Guard: ignore empty results
    if (!trimmed) return

    // Guard: ignore duplicate final events for the same transcript
    if (trimmed === lastSubmittedRef.current) {
      console.info('[STT] Duplicate transcript ignored:', trimmed)
      return
    }

    console.info('[STT] Final transcript received:', trimmed)

    // Populate the textarea so the user can see what was recognised
    const textarea = textareaRef.current
    if (textarea) {
      textarea.value = trimmed
      textarea.style.height = 'auto'
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
    }

    // Record before sending so a re-entrant duplicate event is also blocked
    lastSubmittedRef.current = trimmed

    try {
      // Reuse the single handleSend path — identical to clicking Send
      handleSend(trimmed)
      console.info('[STT] Transcript submitted:', trimmed)
    } catch (err) {
      // On failure keep the text in the textarea and let the user retry
      console.error('[STT] Submission failed:', err)
      // Reset guard so the same phrase can be retried
      lastSubmittedRef.current = ''
    }
  }, [handleSend])

  const {
    isSupported,
    isListening,
    isSpeech,
    interimTranscript,
    error: speechError,
    startListening,
    stopListening,
  } = useSpeechRecognition(handleFinalTranscript)

  // Reset the dedup guard whenever voice mode ends so the same phrase can
  // be spoken again in a new session.
  useEffect(() => {
    if (!isListening) {
      lastSubmittedRef.current = ''
    }
  }, [isListening])

  const handleVoiceToggle = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

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

  const displayText = interimTranscript || (isListening ? 'Listening...' : '')

  return (
    <div className={styles.inputArea}>
      {speechError && (
        <div className={styles.errorBar}>
          <span>{speechError}</span>
        </div>
      )}
      {isListening && !speechError && (
        <div className={styles.listeningBar}>
          <span className={`${styles.listeningDot} ${isSpeech ? styles.active : ''}`} />
          <span className={styles.listeningLabel}>
            {displayText}
          </span>
          <VoiceLevelIndicator level={isSpeech ? 0.6 : 0.15} />
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
          onClick={() => handleSend()}
          disabled={isLoading || isListening}
          title="Send (Enter)"
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  )
}
