const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  hasGoogleApiKey: Boolean(process.env.GOOGLE_API_KEY),
  onBackendStatus: (callback) => {
    ipcRenderer.on('backend:status', (_event, status) => callback(status))
  },
})
