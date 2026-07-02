import Sidebar from '../../components/Sidebar/Sidebar'
import Chat from '../../components/Chat/Chat'
import Settings from '../../components/Settings/Settings'
import BackendStatus from '../../components/BackendStatus/BackendStatus'
import { useChat } from '../../hooks/useChat'
import { useSidebar } from '../../hooks/useSidebar'
import styles from './ChatPage.module.css'

export default function ChatPage() {
  const {
    conversations,
    activeConversation,
    activeId,
    isLoading,
    error,
    createConversation,
    send,
    deleteConversation,
    setActiveId,
  } = useChat()

  const {
    collapsed,
    toggle,
    showSettings,
    openSettings,
    closeSettings,
  } = useSidebar()

  return (
    <div className={styles.layout}>
      <Sidebar
        collapsed={collapsed}
        onToggle={toggle}
        conversations={conversations}
        activeId={activeId}
        onNewChat={createConversation}
        onSelect={setActiveId}
        onDelete={deleteConversation}
        onSettings={openSettings}
      />
      <div className={styles.chatCol}>
        <BackendStatus />
        <Chat
          conversation={activeConversation}
          isLoading={isLoading}
          onSend={send}
        />
      </div>
      <Settings open={showSettings} onClose={closeSettings} />
    </div>
  )
}
