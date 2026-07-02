import { useState, useCallback } from 'react'

export function useSidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const toggle = useCallback(() => setCollapsed(prev => !prev), [])
  const openSettings = useCallback(() => setShowSettings(true), [])
  const closeSettings = useCallback(() => setShowSettings(false), [])

  return { collapsed, toggle, showSettings, openSettings, closeSettings }
}
