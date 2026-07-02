import { useEffect, useRef } from 'react'
import { MessageSquare } from 'lucide-react'
import Message from '../Message/Message'
import ChatInput from '../ChatInput/ChatInput'
import type { Conversation } from '../../types'
import styles from './Chat.module.css'

interface ChatProps {
  conversation: Conversation | null
  isLoading: boolean
  onSend: (text: string) => void
}

export default function Chat({ conversation, isLoading, onSend }: ChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conversation?.messages.length])

  if (!conversation) {
    return (
      <div className={styles.chat}>
        <div className={styles.emptyState}>
          <MessageSquare size={48} className={styles.emptyIcon} />
          <h2 className={styles.emptyTitle}>Start a conversation</h2>
          <p className={styles.emptySubtitle}>Type a message below to begin.</p>
        </div>
        <ChatInput onSend={onSend} isLoading={isLoading} />
      </div>
    )
  }

  return (
    <div className={styles.chat}>
      <div className={styles.header}>
        <h1 className={styles.headerTitle}>{conversation.title}</h1>
      </div>

      <div className={styles.messageList}>
        <div className={styles.messageContainer}>
          {conversation.messages.map(msg => (
            <Message key={msg.id} message={msg} />
          ))}

          {isLoading && (
            <div className={styles.typingIndicator}>
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  )
}
