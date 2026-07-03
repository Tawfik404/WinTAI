import { useState, useCallback, useRef, useEffect } from 'react'
import speechRecognition from '../services/speechRecognition'

interface SpeechRecognitionHook {
  isSupported: boolean
  isListening: boolean
  transcript: string
  interimTranscript: string
  error: string | null
  audioLevel: number
  startListening: () => void
  stopListening: () => void
  cancelListening: () => void
}

export function useSpeechRecognition(
  onFinalTranscript?: (text: string) => void,
): SpeechRecognitionHook {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)
  const onFinalRef = useRef(onFinalTranscript)
  const errorTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const rafRef = useRef(0)

  onFinalRef.current = onFinalTranscript

  useEffect(() => {
    return () => {
      if (speechRecognition.isListening) {
        speechRecognition.cancel()
      }
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const clearErrorAfterDelay = useCallback(() => {
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    errorTimerRef.current = setTimeout(() => setError(null), 5000)
  }, [])

  const startListening = useCallback(() => {
    setError(null)
    setTranscript('')
    setInterimTranscript('')
    setAudioLevel(0)
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)

    if (!speechRecognition.isSupported) {
      setError('Speech recognition is not supported in this browser')
      return
    }

    const fadeLevel = () => {
      setAudioLevel(prev => Math.max(0, prev - 0.02))
      rafRef.current = requestAnimationFrame(fadeLevel)
    }
    rafRef.current = requestAnimationFrame(fadeLevel)

    speechRecognition.start({
      onResult: (text, isFinal) => {
        if (isFinal) {
          setTranscript(text)
          setInterimTranscript('')
          onFinalRef.current?.(text)
        } else {
          setInterimTranscript(text)
        }
      },
      onEnd: () => {
        setIsListening(false)
        setAudioLevel(0)
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
      },
      onError: (msg) => {
        setIsListening(false)
        setAudioLevel(0)
        setError(msg)
        setInterimTranscript('')
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
        clearErrorAfterDelay()
      },
      onAudioLevel: (level) => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
        setAudioLevel(level)
        const fadeLevel = () => {
          setAudioLevel(prev => Math.max(0, prev - 0.015))
          rafRef.current = requestAnimationFrame(fadeLevel)
        }
        rafRef.current = requestAnimationFrame(fadeLevel)
      },
    })

    setIsListening(true)
  }, [clearErrorAfterDelay])

  const stopListening = useCallback(() => {
    speechRecognition.stop()
    setIsListening(false)
    setAudioLevel(0)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
  }, [])

  const cancelListening = useCallback(() => {
    speechRecognition.cancel()
    setIsListening(false)
    setInterimTranscript('')
    setAudioLevel(0)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
  }, [])

  return {
    isSupported: speechRecognition.isSupported,
    isListening,
    transcript,
    interimTranscript,
    error,
    audioLevel,
    startListening,
    stopListening,
    cancelListening,
  }
}
