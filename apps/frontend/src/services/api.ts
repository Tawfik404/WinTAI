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

export async function sendTts(text: string): Promise<ArrayBuffer | null> {
  try {
    const response = await http.post('/api/tts', { text }, {
      responseType: 'arraybuffer',
      timeout: 15000,
    })
    if (response.headers['x-tts-unavailable'] === '1') return null
    return response.data as ArrayBuffer
  } catch {
    return null
  }
}
