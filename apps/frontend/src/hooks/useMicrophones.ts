import { useState, useEffect, useCallback } from 'react'
import {
  enumerateBrowserMicrophones,
  getSelectedMicrophone,
  selectMicrophone,
  type MicrophoneDevice,
} from '../services/microphone'

export function useMicrophones() {
  const [microphones, setMicrophones] = useState<MicrophoneDevice[]>([])
  const [selected, setSelected] = useState<MicrophoneDevice | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [devices, saved] = await Promise.all([
        enumerateBrowserMicrophones(),
        getSelectedMicrophone().catch(() => null),
      ])

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

  return { microphones, selected, loading, error, select, refresh }
}
