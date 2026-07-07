import { useState, useEffect, useCallback, useRef } from 'react'
import {
  enumerateBrowserMicrophones,
  getSelectedMicrophone,
  selectMicrophone,
  measureMicLevel,
  type MicrophoneDevice,
} from '../services/microphone'

export function useMicrophones() {
  const [microphones, setMicrophones] = useState<MicrophoneDevice[]>([])
  const [selected, setSelected] = useState<MicrophoneDevice | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [micLevels, setMicLevels] = useState<Record<string, number>>({})
  const cancelledRef = useRef(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    cancelledRef.current = false

    try {
      const [devices, saved] = await Promise.all([
        enumerateBrowserMicrophones(),
        getSelectedMicrophone().catch(() => null),
      ])

      if (cancelledRef.current) return
      setMicrophones(devices)

      if (saved) {
        const match = devices.find(d => d.id === saved.id)
        if (match) {
          setSelected(match)
        } else {
          const defaultDev = devices.find(d => d.default) || devices[0] || null
          setSelected(defaultDev)
        }
      } else {
        const defaultDev = devices.find(d => d.default) || devices[0] || null
        setSelected(defaultDev)
      }
    } catch (e) {
      setError((e as Error).message || 'Failed to load microphones')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // Measure levels for all mics after they load
  useEffect(() => {
    if (microphones.length === 0 || loading) return

    let active = true
    const levels: Record<string, number> = {}

    ;(async () => {
      for (const mic of microphones) {
        if (!active) break
        const level = await measureMicLevel(mic.id)
        if (active) levels[mic.id] = level
      }
      if (active) setMicLevels(levels)
    })()

    return () => { active = false }
  }, [microphones, loading])

  const select = useCallback(
    async (deviceId: string) => {
      setError(null)
      try {
        await selectMicrophone(deviceId)
        const dev = microphones.find(d => d.id === deviceId) || null
        setSelected(dev)
      } catch (e) {
        setError((e as Error).message || 'Failed to save microphone selection')
      }
    },
    [microphones],
  )

  const refresh = useCallback(() => {
    load()
  }, [load])

  return { microphones, selected, loading, error, select, refresh, micLevels }
}
