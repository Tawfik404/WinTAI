export interface HealthResponse {
  status: string
}

export interface ToolInfo {
  id: string
  name: string
  description: string
}

export interface ToolData {
  tool: ToolInfo
  status: string
  reason: string | null
  execution: Record<string, unknown> | null
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  toolData?: ToolData | null
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: number
}

export interface SendMessageResponse {
  response: string
  tool?: ToolInfo
  status?: string
  reason?: string
  execution?: Record<string, unknown> | null
  tts?: string
}
