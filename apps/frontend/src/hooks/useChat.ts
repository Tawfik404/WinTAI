import { useState, useCallback } from 'react'
import type { Message, Conversation } from '../types'
import { sendMessage } from '../services/api'
import { speak } from '../services/tts'

let messageId = 0
const nextId = () => `msg_${++messageId}_${Date.now()}`
let convId = 0
const nextConvId = () => `conv_${++convId}_${Date.now()}`

function truncate(text: string, max = 40): string {
  if (text.length <= max) return text
  return text.slice(0, max) + '...'
}

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const activeConversation = conversations.find(c => c.id === activeId) ?? null

  const createConversation = useCallback(() => {
    const id = nextConvId()
    const conv: Conversation = {
      id,
      title: 'New conversation',
      messages: [],
      createdAt: Date.now(),
    }
    setConversations(prev => [conv, ...prev])
    setActiveId(id)
    setError(null)
    return id
  }, [])

  const send = useCallback(async (text: string) => {
    if (!text.trim()) return
    setError(null)

    let convId = activeId
    if (!convId) {
      convId = createConversation()
    }

    const userMsg: Message = {
      id: nextId(),
      role: 'user',
      content: text.trim(),
      timestamp: Date.now(),
    }

    setConversations(prev => prev.map(c => {
      if (c.id !== convId) return c
      const newTitle = c.messages.length === 0 ? truncate(text.trim()) : c.title
      return {
        ...c,
        title: newTitle,
        messages: [...c.messages, userMsg],
      }
    }))

    setIsLoading(true)

    try {
      const res = await sendMessage(text)
      const content = res.response || JSON.stringify(res, null, 2)

      const assistantMsg: Message = {
        id: nextId(),
        role: 'assistant',
        content,
        timestamp: Date.now(),
      }

      setConversations(prev => prev.map(c => {
        if (c.id !== convId) return c
        return { ...c, messages: [...c.messages, assistantMsg] }
      }))

      if (res.tts) {
        speak(res.tts)
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend'
      setError(message)

      const errorMsg: Message = {
        id: nextId(),
        role: 'assistant',
        content: `Error: ${message}`,
        timestamp: Date.now(),
      }

      setConversations(prev => prev.map(c => {
        if (c.id !== convId) return c
        return { ...c, messages: [...c.messages, errorMsg] }
      }))
    } finally {
      setIsLoading(false)
    }
  }, [activeId, createConversation])

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeId === id) {
      setActiveId(prev => {
        const remaining = conversations.filter(c => c.id !== id)
        return remaining.length > 0 ? remaining[0].id : null
      })
    }
  }, [activeId, conversations])

  return {
    conversations,
    activeConversation,
    activeId,
    isLoading,
    error,
    createConversation,
    send,
    deleteConversation,
    setActiveId,
  }
}
