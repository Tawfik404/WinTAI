export interface HealthResponse {
  status: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}

export interface SendMessageResponse {
  response: string
  tool?: string
  status?: string
  reason?: string
}
