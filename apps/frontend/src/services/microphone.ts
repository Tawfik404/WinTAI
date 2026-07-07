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

export async function measureMicLevel(deviceId: string): Promise<number> {
  try {
    const constraints: MediaStreamConstraints = {
      audio: deviceId === 'default' ? true : { deviceId: { exact: deviceId } },
    }
    const stream = await navigator.mediaDevices.getUserMedia(constraints)
    const audioContext = new AudioContext()
    await audioContext.resume()
    const source = audioContext.createMediaStreamSource(stream)
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    source.connect(analyser)

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    let peak = 0

    for (let i = 0; i < 6; i++) {
      await new Promise(r => setTimeout(r, 50))
      analyser.getByteTimeDomainData(dataArray)
      let sum = 0
      for (let j = 0; j < dataArray.length; j++) {
        const val = dataArray[j] / 128 - 1
        sum += val * val
      }
      peak = Math.max(peak, Math.sqrt(sum / dataArray.length))
    }

    source.disconnect()
    await audioContext.close()
    stream.getTracks().forEach(t => t.stop())
    return peak
  } catch {
    return 0
  }
}
