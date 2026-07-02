import http from '../lib/http'
import type { HealthResponse, SendMessageResponse } from '../types'

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await http.get<HealthResponse>('/health')
  return data
}

export async function sendMessage(text: string): Promise<SendMessageResponse> {
  const { data } = await http.post<SendMessageResponse>('/api/chat', { message: text })
  return data
}
