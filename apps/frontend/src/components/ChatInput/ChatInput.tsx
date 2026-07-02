import { useRef, useCallback, useEffect } from 'react'
import { ArrowUp } from 'lucide-react'
import styles from './ChatInput.module.css'

interface ChatInputProps {
  onSend: (text: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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
      <div className={styles.inputContainer}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Type a message..."
          rows={1}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={isLoading}
        />
        <button
          className={styles.sendBtn}
          onClick={handleSend}
          disabled={isLoading}
          title="Send (Enter)"
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  )
}
