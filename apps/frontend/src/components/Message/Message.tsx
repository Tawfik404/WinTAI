import type { Message as MessageType } from '../../types'
import styles from './Message.module.css'

interface MessageProps {
  message: MessageType
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`${styles.row} ${isUser ? styles.userRow : styles.assistantRow}`}>
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.assistantBubble}`}>
        <FormattedContent content={message.content} />
      </div>
    </div>
  )
}

function FormattedContent({ content }: { content: string }) {
  if (!content.startsWith('Error:') && !content.startsWith('{') && !content.startsWith('[')) {
    return <>{content}</>
  }

  if (content.startsWith('Error:')) {
    return <span style={{ color: 'var(--danger)' }}>{content}</span>
  }

  try {
    const parsed = JSON.parse(content)
    if (parsed.tool || parsed.status) {
      return (
        <>
          {parsed.tool && <><span style={{ opacity: 0.5 }}>Tool:</span> {parsed.tool}<br /></>}
          {parsed.status && <><span style={{ opacity: 0.5 }}>Status:</span> {parsed.status}<br /></>}
          {parsed.reason && <><span style={{ opacity: 0.5 }}>Reason:</span> {parsed.reason}</>}
        </>
      )
    }
    const text = typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2)
    return <>{text}</>
  } catch {
    return <>{content}</>
  }
}
