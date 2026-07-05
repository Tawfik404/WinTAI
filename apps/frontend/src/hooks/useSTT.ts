import { useState, useCallback, useRef, useEffect } from 'react'
import sttService from '../services/stt'
import { getSelectedMicrophone } from '../services/microphone'

interface STTHook {
  isSupported: boolean
  isListening: boolean
  status: string
  transcript: string
  interimTranscript: string
  error: string | null
  audioLevel: number
  startListening: (deviceId?: string) => Promise<void>
  stopListening: () => void
  cancelListening: () => void
}

export function useSTT(
  onFinalTranscript?: (text: string) => void,
): STTHook {
  const [isListening, setIsListening] = useState(false)
  const [status, setStatus] = useState('idle')
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
      if (sttService.isListening) {
        sttService.cancel()
      }
      if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const clearErrorAfterDelay = useCallback(() => {
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)
    errorTimerRef.current = setTimeout(() => setError(null), 5000)
  }, [])

  const startListening = useCallback(async (deviceId?: string) => {
    setError(null)
    setTranscript('')
    setInterimTranscript('')
    setAudioLevel(0)
    setStatus('connecting')
    if (errorTimerRef.current) clearTimeout(errorTimerRef.current)

    if (!sttService.isSupported) {
      setError('Speech recognition is not supported in this browser')
      setStatus('error')
      return
    }

    let resolvedDeviceId = deviceId
    if (!resolvedDeviceId) {
      try {
        const saved = await getSelectedMicrophone()
        resolvedDeviceId = saved.id
      } catch {
        resolvedDeviceId = 'default'
      }
    }

    const fadeLevel = () => {
      setAudioLevel(prev => Math.max(0, prev - 0.02))
      rafRef.current = requestAnimationFrame(fadeLevel)
    }
    rafRef.current = requestAnimationFrame(fadeLevel)

    sttService.start({
      onPartial: (text: string) => {
        setInterimTranscript(text)
      },
      onFinal: (text: string) => {
        setTranscript(text)
        setInterimTranscript('')
      },
      onDone: (text: string) => {
        setIsListening(false)
        setStatus('idle')
        setAudioLevel(0)
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
        if (text) {
          setTranscript(text)
          onFinalRef.current?.(text)
        }
      },
      onError: (msg: string) => {
        setIsListening(false)
        setStatus('error')
        setAudioLevel(0)
        setError(msg)
        setInterimTranscript('')
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
        clearErrorAfterDelay()
      },
      onAudioLevel: (level: number) => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current)
        setAudioLevel(level)
        const fadeLevel = () => {
          setAudioLevel(prev => Math.max(0, prev - 0.015))
          rafRef.current = requestAnimationFrame(fadeLevel)
        }
        rafRef.current = requestAnimationFrame(fadeLevel)
      },
    }, resolvedDeviceId)

    setIsListening(true)
  }, [clearErrorAfterDelay])

  const stopListening = useCallback(() => {
    sttService.stop()
    setIsListening(false)
    setStatus('processing')
    setAudioLevel(0)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
  }, [])

  const cancelListening = useCallback(() => {
    sttService.cancel()
    setIsListening(false)
    setStatus('idle')
    setInterimTranscript('')
    setAudioLevel(0)
    if (rafRef.current) cancelAnimationFrame(rafRef.current)
  }, [])

  return {
    isSupported: sttService.isSupported,
    isListening,
    status,
    transcript,
    interimTranscript,
    error,
    audioLevel,
    startListening,
    stopListening,
    cancelListening,
  }
}
