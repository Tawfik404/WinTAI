import { Bot, PanelLeftClose, PanelLeft, Plus, Settings } from 'lucide-react'
import ConversationItem from '../ConversationItem/ConversationItem'
import type { Conversation } from '../../types'
import styles from './Sidebar.module.css'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  conversations: Conversation[]
  activeId: string | null
  onNewChat: () => void
  onSelect: (id: string) => void
  onDelete: (id: string) => void
  onSettings: () => void
}

export default function Sidebar({
  collapsed,
  onToggle,
  conversations,
  activeId,
  onNewChat,
  onSelect,
  onDelete,
  onSettings,
}: SidebarProps) {
  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : styles.expanded}`}>
      <div className={styles.header}>
        <div className={styles.logo}>
          <Bot size={22} className={styles.logoIcon} />
          {!collapsed && <span>WinTAI</span>}
        </div>
        <button className={styles.collapseBtn} onClick={onToggle} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
        </button>
      </div>

      <button
        className={`${styles.newChatBtn} ${collapsed ? styles.collapsedNewChat : ''}`}
        onClick={onNewChat}
        title="New conversation"
      >
        <Plus size={18} />
        {!collapsed && <span>New Chat</span>}
      </button>

      <div className={styles.conversationList}>
        {conversations.map(conv => (
          <ConversationItem
            key={conv.id}
            conversation={conv}
            active={conv.id === activeId}
            collapsed={collapsed}
            onSelect={() => onSelect(conv.id)}
            onDelete={() => onDelete(conv.id)}
          />
        ))}
      </div>

      <div className={styles.bottomSection}>
        <button
          className={`${styles.settingsBtn} ${collapsed ? styles.collapsedSettingsBtn : ''}`}
          onClick={onSettings}
          title="Settings"
        >
          <Settings size={18} />
          {!collapsed && <span>Settings</span>}
        </button>
      </div>
    </aside>
  )
}
