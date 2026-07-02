const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  onBackendStatus: (callback) => {
    ipcRenderer.on('backend:status', (_event, status) => callback(status))
  },
})
