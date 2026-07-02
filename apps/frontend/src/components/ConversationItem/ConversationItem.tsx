import { MessageSquare, X } from 'lucide-react'
import type { Conversation } from '../../types'
import styles from './ConversationItem.module.css'

interface ConversationItemProps {
  conversation: Conversation
  active: boolean
  collapsed: boolean
  onSelect: () => void
  onDelete: () => void
}

export default function ConversationItem({
  conversation,
  active,
  collapsed,
  onSelect,
  onDelete,
}: ConversationItemProps) {
  return (
    <div
      className={`${styles.item} ${active ? styles.active : ''}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onSelect() }}
    >
      <MessageSquare size={16} className={styles.icon} />
      {!collapsed && (
        <>
          <span className={styles.title}>{conversation.title}</span>
          <button
            className={styles.deleteBtn}
            onClick={e => { e.stopPropagation(); onDelete() }}
            title="Delete conversation"
          >
            <X size={14} />
          </button>
        </>
      )}
    </div>
  )
}
