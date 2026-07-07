export type SpeechEventType =
  | 'started'
  | 'stopped'
  | 'interim'
  | 'final'
  | 'ended'
  | 'error'

export interface SpeechEvent {
  type: SpeechEventType
  text?: string
  error?: string
}

export type SpeechEventHandler = (event: SpeechEvent) => void

class SpeechRecognitionService {
  private _isListening = false
  private _userStopped = false
  private handler: SpeechEventHandler | null = null
  private ws: WebSocket | null = null
  private audioContext: AudioContext | null = null
  private mediaStream: MediaStream | null = null
  private workletNode: AudioWorkletNode | null = null
  private processor: ScriptProcessorNode | null = null
  private _usingWorklet = false
  private _language = 'en-US'

  get isListening(): boolean {
    return this._isListening
  }

  get isSupported(): boolean {
    return true
  }

  setLanguage(lang: string): void {
    this._language = lang
  }

  onEvent(handler: SpeechEventHandler): void {
    this.handler = handler
  }

  private _emit(event: SpeechEvent): void {
    this.handler?.(event)
  }

  async start(): Promise<void> {
    if (this._isListening) return
    this._userStopped = false

    try {
      // 1. Request microphone permission first
      this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // 2. Open WebSocket connection to local STT endpoint
      this.ws = new WebSocket('ws://127.0.0.1:8000/api/stt/ws')
      this.ws.binaryType = 'arraybuffer'

      await new Promise<void>((resolve, reject) => {
        if (!this.ws) return reject(new Error('WebSocket not created'))

        const onOpen = () => {
          this.ws?.removeEventListener('open', onOpen)
          this.ws?.removeEventListener('error', onError)
          resolve()
        }

        const onError = (e: Event) => {
          this.ws?.removeEventListener('open', onOpen)
          this.ws?.removeEventListener('error', onError)
          reject(new Error('Failed to connect to local speech recognition service'))
        }

        this.ws.addEventListener('open', onOpen)
        this.ws.addEventListener('error', onError)
      })

      // Send start message
      this.ws.send(JSON.stringify({ type: 'start' }))

      // 3. Setup AudioContext and capture node (downsample to 16kHz for Moonshine)
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
      this.audioContext = new AudioCtx({ sampleRate: 16000 })
      await this.audioContext.resume()
      const source = this.audioContext.createMediaStreamSource(this.mediaStream)
      const ws = this.ws

      // Prefer AudioWorkletNode (modern, no deprecation); fall back to ScriptProcessorNode
      try {
        const processorCode = [
          'class AudioCaptureProcessor extends AudioWorkletProcessor {',
          '  process(inputs, _outputs, _parameters) {',
          '    const input = inputs[0]',
          '    if (input && input.length > 0) {',
          '      const channelData = input[0]',
          '      this.port.postMessage(channelData.slice(), [channelData.buffer])',
          '    }',
          '    return true',
          '  }',
          '}',
          "registerProcessor('audio-capture-processor', AudioCaptureProcessor)",
        ].join('\n')

        const blob = new Blob([processorCode], { type: 'application/javascript' })
        const url = URL.createObjectURL(blob)
        await this.audioContext.audioWorklet.addModule(url)
        URL.revokeObjectURL(url)

        this.workletNode = new AudioWorkletNode(this.audioContext, 'audio-capture-processor')
        this.workletNode.port.onmessage = (e: MessageEvent<Float32Array>) => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(e.data.buffer as ArrayBuffer)
          }
        }

        source.connect(this.workletNode)
        this._usingWorklet = true
      } catch {
        // Fallback: ScriptProcessorNode (deprecated but works everywhere)
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1)
        this.processor.onaudioprocess = (e) => {
          if (!ws || ws.readyState !== WebSocket.OPEN) return
          ws.send(e.inputBuffer.getChannelData(0).buffer)
        }
        source.connect(this.processor)
        this.processor.connect(this.audioContext.destination)
        this._usingWorklet = false
      }

      // 4. Set up WebSocket message receiver
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          switch (data.type) {
            case 'status':
              if (data.status === 'listening') {
                this._isListening = true
                console.info('Speech recognition started via local backend VAD')
                this._emit({ type: 'started' })
              }
              break
            case 'partial':
              // Moonshine real-time partial result during active speech — show in listening bar
              this._emit({ type: 'interim', text: data.text })
              break
            case 'transcript':
              // VAD-finalized complete speech segment — this IS the final transcript, auto-submit
              console.info('[STT] Final transcript received from VAD segment:', data.text)
              this._emit({ type: 'final', text: data.text })
              break
            case 'done':
              // Backend acknowledged manual stop — emit final for any remaining accumulated text
              if (data.text) {
                console.info('[STT] Final transcript from stop:', data.text)
                this._emit({ type: 'final', text: data.text })
              }
              break
            case 'error':
              console.error('STT WebSocket error message:', data.error)
              this._emit({ type: 'error', error: data.error })
              this.stop()
              break
          }
        } catch (e) {
          console.error('Failed to parse STT websocket message', e)
        }
      }

      this.ws.onclose = () => {
        console.info('STT WebSocket closed')
        const userStopped = this._userStopped
        this.cleanup()
        if (!userStopped) {
          this._emit({ type: 'stopped' })
          this._emit({ type: 'ended' })
        }
      }

      this.ws.onerror = (e) => {
        console.error('STT WebSocket error', e)
        this._emit({ type: 'error', error: 'Speech Recognition Service error' })
        this.stop()
      }

    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to start speech recognition.'
      console.error('Speech recognition failed to start', message)
      this.cleanup()
      this._emit({ type: 'error', error: message })
      throw error
    }
  }

  stop(): void {
    if (!this._isListening && !this.ws) return
    this._userStopped = true
    this._isListening = false
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({ type: 'stop' }))
      } catch (e) {
        // Ignore
      }
    }
    this.cleanup()
    this._emit({ type: 'stopped' })
    this._emit({ type: 'ended' })
  }

  private cleanup(): void {
    this._isListening = false

    if (this.workletNode) {
      try {
        this.workletNode.port.onmessage = null
        this.workletNode.disconnect()
      } catch (e) {}
      this.workletNode = null
    }

    if (this.processor) {
      try {
        this.processor.disconnect()
      } catch (e) {}
      this.processor.onaudioprocess = null
      this.processor = null
    }

    if (this.audioContext) {
      if (this.audioContext.state !== 'closed') {
        try {
          void this.audioContext.close()
        } catch (e) {}
      }
      this.audioContext = null
    }

    if (this.mediaStream) {
      try {
        this.mediaStream.getTracks().forEach((track) => track.stop())
      } catch (e) {}
      this.mediaStream = null
    }

    if (this.ws) {
      try {
        this.ws.onmessage = null
        this.ws.onclose = null
        this.ws.onerror = null
        if (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN) {
          this.ws.close()
        }
      } catch (e) {}
      this.ws = null
    }
  }

  destroy(): void {
    this.stop()
    this.handler = null
  }
}

const speechRecognitionService = new SpeechRecognitionService()
export default speechRecognitionService
