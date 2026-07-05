import http from '../lib/http'

export interface MicrophoneDevice {
  id: string
  name: string
  default: boolean
}

async function ensureMicPermission(): Promise<void> {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    stream.getTracks().forEach(t => t.stop())
  } catch {
    // permission already denied or not available — proceed with whatever we have
  }
}

export async function enumerateBrowserMicrophones(): Promise<MicrophoneDevice[]> {
  let devices = await navigator.mediaDevices.enumerateDevices()
  const hasLabels = devices.some(d => d.kind === 'audioinput' && d.label)

  if (!hasLabels) {
    await ensureMicPermission()
    devices = await navigator.mediaDevices.enumerateDevices()
  }

  const audioInputs = devices.filter(d => d.kind === 'audioinput')

  const mapped = audioInputs.map(d => ({
    id: d.deviceId,
    name: d.label || `Microphone ${d.deviceId.slice(0, 8)}`,
    default: d.deviceId === 'default',
  }))

  if (mapped.length === 0) {
    mapped.push({ id: 'default', name: 'System Default', default: true })
  }

  return mapped
}

export async function getSelectedMicrophone(): Promise<MicrophoneDevice> {
  const { data } = await http.get<MicrophoneDevice>('/api/stt/microphone')
  return data
}

export async function selectMicrophone(deviceId: string): Promise<void> {
  await http.put('/api/stt/microphone', { deviceId })
}
