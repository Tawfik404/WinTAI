type STTCallback = {
  onPartial?: (text: string) => void
  onFinal?: (text: string) => void
  onDone?: (text: string) => void
  onError?: (error: string) => void
  onAudioLevel?: (level: number) => void
}

type STTStatus = 'idle' | 'connecting' | 'listening' | 'processing' | 'error'

function createAudioCaptureProcessorBlob(): string {
  const code = `
class AudioCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
  }

  process(inputs, _outputs, _parameters) {
    const input = inputs[0]
    if (input && input.length > 0) {
      const channelData = input[0]
      this.port.postMessage(channelData.slice(), [channelData.buffer])
    }
    return true
  }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor)
`
  const blob = new Blob([code], { type: 'application/javascript' })
  return URL.createObjectURL(blob)
}

class STTService {
  private ws: WebSocket | null = null
  private mediaStream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private sourceNode: MediaStreamAudioSourceNode | null = null
  private workletNode: AudioWorkletNode | null = null
  private processorFallback: ScriptProcessorNode | null = null
  private analyserNode: AnalyserNode | null = null
  private animationId: number = 0
  private callbacks: STTCallback | null = null
  private _status: STTStatus = 'idle'
  private _error: string | null = null
  private wsUrl: string = ''
  private usingWorklet: boolean = false
  private _deviceId: string = 'default'

  get status(): STTStatus {
    return this._status
  }

  get error(): string | null {
    return this._error
  }

  get isListening(): boolean {
    return this._status === 'listening'
  }

  get isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof AudioContext !== 'undefined'
    )
  }

  start(callbacks: STTCallback, deviceId?: string): void {
    if (this._status === 'listening') return

    this.callbacks = callbacks
    this._error = null
    this._status = 'connecting'

    this.wsUrl = 'ws://127.0.0.1:8000/api/stt/ws'
    this._deviceId = deviceId || 'default'

    this._connectWebSocket()
  }

  private _connectWebSocket(): void {
    try {
      this.ws = new WebSocket(this.wsUrl)
    } catch (e) {
      this._handleError(`WebSocket connection failed: ${(e as Error).message}`)
      return
    }

    this.ws.binaryType = 'arraybuffer'

    this.ws.onopen = () => {
      this._requestMic()
    }

    this.ws.onmessage = (event: MessageEvent) => {
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data)
          this._handleMessage(msg)
        } catch {
          // ignore non-JSON messages
        }
      }
    }

    this.ws.onclose = () => {
      this._cleanup()
      if (this._status === 'connecting' || this._status === 'listening') {
        this._handleError('Connection to speech service lost')
      }
      this._status = 'idle'
    }

    this.ws.onerror = () => {
      this._handleError('WebSocket connection error')
    }
  }

  stop(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'stop' }))
      this._status = 'processing'
    } else {
      this._cleanup()
      this._status = 'idle'
    }
  }

  cancel(): void {
    this._cleanup()
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    this._status = 'idle'
  }

  private _requestMic(): void {
    const onStream = (stream: MediaStream) => {
      this.mediaStream = stream
      this._startCapture()
    }

    const onError = (err: DOMException) => {
      if (err.name === 'NotFoundError' || err.name === 'NotAllowedError') {
        this._handleError(
          err.name === 'NotFoundError'
            ? 'No microphone found. Check your microphone.'
            : 'Microphone permission denied. Allow access in browser settings.',
        )
      } else {
        this._handleError(`Microphone error: ${err.message}`)
      }
    }

    const constraints: MediaStreamConstraints = {
      audio: this._deviceId === 'default'
        ? true
        : { deviceId: { exact: this._deviceId } },
    }

    navigator.mediaDevices
      .getUserMedia(constraints)
      .then(onStream)
      .catch((firstErr: DOMException) => {
        if (firstErr.name === 'NotFoundError' || firstErr.name === 'NotAllowedError') {
          onError(firstErr)
          return
        }
        navigator.mediaDevices
          .getUserMedia({ audio: true })
          .then(onStream)
          .catch(onError)
      })
  }

  private async _startCapture(): Promise<void> {
    if (!this.mediaStream) return

    try {
      this.audioContext = new AudioContext({ sampleRate: 16000 })
    } catch {
      this.audioContext = new AudioContext()
    }

    const ctx = this.audioContext

    // AudioContext is created in a suspended state outside a user
    // gesture.  Resuming *before* any await preserves the gesture
    // context so the browser allows audio processing to start.
    try {
      await ctx.resume()
    } catch {
      // resume can fail if called after close; ignore
    }

    this.sourceNode = ctx.createMediaStreamSource(this.mediaStream)

    this.analyserNode = ctx.createAnalyser()
    this.analyserNode.fftSize = 256
    this.sourceNode.connect(this.analyserNode)

    try {
      const url = createAudioCaptureProcessorBlob()
      await ctx.audioWorklet.addModule(url)
      URL.revokeObjectURL(url)

      this.workletNode = new AudioWorkletNode(ctx, 'audio-capture-processor')
      this.analyserNode.connect(this.workletNode)
      this.usingWorklet = true

      const ws = this.ws
      this.workletNode.port.onmessage = (event: MessageEvent) => {
        if (this._status !== 'listening' || !ws || ws.readyState !== WebSocket.OPEN) return
        ws.send(event.data)
      }
    } catch {
      this._fallbackCapture(ctx)
    }

    this._startLevelMeter()

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'start' }))
    }
  }

  private _fallbackCapture(ctx: AudioContext): void {
    const bufferSize = 4096

    this.processorFallback = ctx.createScriptProcessor(bufferSize, 1, 1)
    this.analyserNode!.connect(this.processorFallback)
    this.usingWorklet = false

    const silentGain = ctx.createGain()
    silentGain.gain.value = 0
    this.processorFallback.connect(silentGain)
    silentGain.connect(ctx.destination)

    const ws = this.ws

    this.processorFallback.onaudioprocess = (event: AudioProcessingEvent) => {
      if (this._status !== 'listening' || !ws || ws.readyState !== WebSocket.OPEN) return

      const input = event.inputBuffer.getChannelData(0)
      ws.send(input.slice().buffer)
    }
  }

  private _startLevelMeter(): void {
    if (!this.analyserNode) return

    const bufferLength = this.analyserNode.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const poll = () => {
      if (this._status !== 'listening' || !this.analyserNode) return
      this.analyserNode.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let i = 0; i < bufferLength; i++) {
        const val = dataArray[i] / 128 - 1
        sum += val * val
      }
      const rms = Math.sqrt(sum / bufferLength)
      this.callbacks?.onAudioLevel?.(Math.min(1, rms * 3))
      this.animationId = requestAnimationFrame(poll)
    }

    this.animationId = requestAnimationFrame(poll)
  }

  private _handleMessage(msg: Record<string, unknown>): void {
    switch (msg.type) {
      case 'status':
        if (msg.status === 'listening') {
          this._status = 'listening'
        }
        break
      case 'partial':
        this.callbacks?.onPartial?.(String(msg.text ?? ''))
        break
      case 'final':
        this.callbacks?.onFinal?.(String(msg.text ?? ''))
        break
      case 'done':
        this._status = 'idle'
        this.callbacks?.onDone?.(String(msg.text ?? ''))
        break
      case 'error':
        this._handleError(String(msg.error ?? 'Unknown STT error'))
        break
    }
  }

  private _handleError(error: string): void {
    this._error = error
    this._status = 'error'
    this._cleanup()
    this.callbacks?.onError?.(error)
  }

  private _cleanup(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
      this.animationId = 0
    }

    if (this.workletNode) {
      this.workletNode.disconnect()
      this.workletNode = null
    }

    if (this.processorFallback) {
      this.processorFallback.disconnect()
      this.processorFallback = null
    }

    if (this.analyserNode) {
      this.analyserNode.disconnect()
      this.analyserNode = null
    }

    if (this.sourceNode) {
      this.sourceNode.disconnect()
      this.sourceNode = null
    }

    if (this.audioContext) {
      this.audioContext.close().catch(() => {})
      this.audioContext = null
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop())
      this.mediaStream = null
    }

    if (this.ws) {
      this.ws.onopen = null
      this.ws.onmessage = null
      this.ws.onclose = null
      this.ws.onerror = null
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close()
      }
      this.ws = null
    }

    this.usingWorklet = false
  }
}

const sttService = new STTService()
export default sttService
