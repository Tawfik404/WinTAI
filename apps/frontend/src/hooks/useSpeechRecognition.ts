import { useState, useCallback, useRef, useEffect } from 'react'
import speechService from '../services/speechRecognition'

interface SpeechRecognitionHook {
  isSupported: boolean
  isListening: boolean
  isSpeech: boolean
  status: string
  interimTranscript: string
  error: string | null
  startListening: () => void
  stopListening: () => void
}

export function useSpeechRecognition(
  onFinalTranscript?: (text: string) => void,
): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false)
  const [isSpeech, setIsSpeech] = useState(false)
  const [status, setStatus] = useState('idle')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const onFinalRef = useRef(onFinalTranscript)
  const [isSupported] = useState(() => speechService.isSupported)
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  onFinalRef.current = onFinalTranscript

  useEffect(() => {
    speechService.onEvent((event) => {
      switch (event.type) {
        case 'started':
          setIsListening(true)
          setIsSpeech(false)
          setStatus('listening')
          break

        case 'stopped':
          setIsListening(false)
          setIsSpeech(false)
          setStatus('idle')
          setInterimTranscript('')
          if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
          break

        case 'interim':
          setIsSpeech(true)
          setInterimTranscript(event.text ?? '')
          break

        case 'final':
          setIsSpeech(false)
          setInterimTranscript('')
          if (event.text) {
            onFinalRef.current?.(event.text)
          }
          break

        case 'ended':
          setIsSpeech(false)
          break

        case 'error':
          setIsListening(false)
          setIsSpeech(false)
          setStatus('error')
          setError(event.error ?? 'Speech recognition error')
          setInterimTranscript('')
          if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
          errorTimerRef.current = setTimeout(() => setError(null), 5000)
          break
      }
    })
  }, [])

  useEffect(() => {
    return () => {
      speechService.destroy()
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    }
  }, [])

  const startListening = useCallback(() => {
    setError(null)
    setInterimTranscript('')
    setStatus('connecting')
    setIsListening(true)
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    void speechService.start().catch((err) => {
      setIsListening(false)
      setIsSpeech(false)
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Speech recognition failed to start')
    })
  }, [])

  const stopListening = useCallback(() => {
    speechService.stop()
  }, [])

  return {
    isSupported,
    isListening,
    isSpeech,
    status,
    interimTranscript,
    error,
    startListening,
    stopListening,
  }
}

