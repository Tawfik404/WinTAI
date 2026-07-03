type SpeechRecognitionCallback = {
  onResult: (transcript: string, isFinal: boolean) => void
  onEnd: () => void
  onError: (error: string) => void
  onAudioLevel?: (level: number) => void
}

class SpeechRecognitionService {
  private recognition: SpeechRecognition | null = null
  private callbacks: SpeechRecognitionCallback | null = null
  private _isListening = false
  private destroyed = false

  private mediaStream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private analyserNode: AnalyserNode | null = null
  private animationId: number = 0

  get isListening(): boolean {
    return this._isListening
  }

  get isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
    )
  }

  start(callbacks: SpeechRecognitionCallback): void {
    if (this._isListening) return
    if (!this.isSupported) {
      callbacks.onError('Speech recognition not supported in this browser')
      return
    }

    this.callbacks = callbacks
    this.destroyed = false

    const requestMic = async (): Promise<MediaStream | null> => {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        return null
      }
      try {
        return await navigator.mediaDevices.getUserMedia({
          audio: { deviceId: 'default' },
        })
      } catch (firstErr) {
        if (
          firstErr instanceof DOMException &&
          (firstErr.name === 'NotFoundError' || firstErr.name === 'NotAllowedError')
        ) {
          throw firstErr
        }
        try {
          return await navigator.mediaDevices.getUserMedia({ audio: true })
        } catch {
          throw firstErr
        }
      }
    }

    requestMic().then(stream => {
      if (this.destroyed) {
        if (stream) stream.getTracks().forEach(t => t.stop())
        return
      }
      if (!stream) {
        callbacks.onError('No microphone found. Check your microphone.')
        return
      }
      this.mediaStream = stream
      this._startLevelMeter(callbacks)
      this._startRecognition(callbacks)
    }).catch(err => {
      this._isListening = false
      this._destroy()
      if (err.name === 'NotFoundError') {
        callbacks.onError('No microphone found. Check your microphone.')
      } else if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        callbacks.onError('Microphone permission denied. Allow access in browser settings.')
      } else {
        callbacks.onError(`Microphone error: ${err.message}`)
      }
    })
  }

  stop(): void {
    if (!this.recognition) return
    this.destroyed = true
    try {
      this.recognition.stop()
    } catch {
      // ignore
    }
    this._cleanup()
  }

  cancel(): void {
    if (!this.recognition) return
    this.destroyed = true
    try {
      this.recognition.abort()
    } catch {
      // ignore
    }
    this._cleanup()
  }

  private _startLevelMeter(callbacks: SpeechRecognitionCallback): void {
    if (!this.mediaStream || !callbacks.onAudioLevel) return

    try {
      this.audioContext = new AudioContext()
      const source = this.audioContext.createMediaStreamSource(this.mediaStream)
      this.analyserNode = this.analyserNode = this.audioContext.createAnalyser()
      this.analyserNode.fftSize = 256
      source.connect(this.analyserNode)

      const bufferLength = this.analyserNode.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      const poll = () => {
        if (this.destroyed || !this.analyserNode) return
        this.analyserNode.getByteTimeDomainData(dataArray)
        let sum = 0
        for (let i = 0; i < bufferLength; i++) {
          const val = dataArray[i] / 128 - 1
          sum += val * val
        }
        const rms = Math.sqrt(sum / bufferLength)
        callbacks.onAudioLevel?.(Math.min(1, rms * 3))
        this.animationId = requestAnimationFrame(poll)
      }

      this.animationId = requestAnimationFrame(poll)
    } catch (e) {
      console.warn('Audio level meter unavailable:', e)
    }
  }

  private _startRecognition(callbacks: SpeechRecognitionCallback): void {
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition
    this.recognition = new SpeechRecognitionAPI()

    this.recognition.continuous = false
    this.recognition.interimResults = true
    this.recognition.lang = 'en-US'

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (this.destroyed) return
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interimTranscript += result[0].transcript
        }
      }

      if (finalTranscript) {
        this._isListening = false
        callbacks.onResult(finalTranscript, true)
      }
      if (interimTranscript) {
        callbacks.onResult(interimTranscript, false)
      }
    }

    this.recognition.onend = () => {
      if (this.destroyed) return
      this._isListening = false
      this._stopLevelMeter()
      this.recognition = null
      this._releaseStream()
      callbacks.onEnd()
    }

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (this.destroyed) return
      this._isListening = false
      this._stopLevelMeter()
      this._releaseStream()

      if (event.error === 'aborted') return

      if (event.error === 'network') {
        this._destroy()
        callbacks.onError(
          'Speech recognition requires an internet connection. ' +
          'Make sure you are online and try again.'
        )
        return
      }

      if (event.error === 'not-allowed') {
        this._destroy()
        callbacks.onError('Microphone permission denied. Allow access in browser settings.')
        return
      }

      let message = 'Speech recognition error'
      switch (event.error) {
        case 'no-speech':
          message = 'No speech detected. Try speaking again.'
          break
        case 'audio-capture':
          message = 'No microphone found. Check your microphone.'
          break
        default:
          message = `Speech error: ${event.error}`
      }
      callbacks.onError(message)
    }

    try {
      this.recognition.start()
      this._isListening = true
    } catch (e) {
      this._isListening = false
      this._stopLevelMeter()
      this._releaseStream()
      this._destroy()
      callbacks.onError('Failed to start speech recognition')
    }
  }

  private _stopLevelMeter(): void {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId)
      this.animationId = 0
    }
    if (this.audioContext) {
      this.audioContext.close().catch(() => {})
      this.audioContext = null
      this.analyserNode = null
    }
  }

  private _releaseStream(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(t => t.stop())
      this.mediaStream = null
    }
  }

  private _destroy(): void {
    this.destroyed = true
    if (this.recognition) {
      try {
        this.recognition.abort()
      } catch {
        // ignore
      }
    }
    this._cleanup()
  }

  private _cleanup(): void {
    if (this.recognition) {
      this.recognition.onresult = null
      this.recognition.onend = null
      this.recognition.onerror = null
    }
    this.recognition = null
    this._isListening = false
    this.callbacks = null
    this._stopLevelMeter()
    this._releaseStream()
  }
}

const speechRecognition = new SpeechRecognitionService()
export default speechRecognition
