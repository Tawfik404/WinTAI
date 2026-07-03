import http from '../lib/http'

let audioContext: AudioContext | null = null

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  return audioContext
}

export async function speak(text: string): Promise<void> {
  if (!text) return

  try {
    const response = await http.post('/api/tts', { text }, {
      responseType: 'arraybuffer',
    })

    if (response.headers['x-tts-unavailable'] === '1') {
      fallbackSpeak(text)
      return
    }

    const wavData = response.data as ArrayBuffer
    if (!wavData || wavData.byteLength === 0) {
      fallbackSpeak(text)
      return
    }

    const ctx = getAudioContext()
    const audioBuffer = await ctx.decodeAudioData(wavData.slice(0))
    const source = ctx.createBufferSource()
    source.buffer = audioBuffer
    source.connect(ctx.destination)
    source.start()
  } catch {
    fallbackSpeak(text)
  }
}

function fallbackSpeak(text: string): void {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'en-US'
  utterance.rate = 1.1
  utterance.pitch = 1.0
  window.speechSynthesis.speak(utterance)
}
