const { app, BrowserWindow, dialog, session } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

let mainWindow
let backendProcess = null
let healthInterval = null

function getAppRoot() {
  if (process.env.VITE_DEV_SERVER_URL) {
    return path.resolve(__dirname, '../../..')
  }
  return path.join(process.resourcesPath, 'app')
}

function sendStatus(status) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('backend:status', status)
  }
}

function startBackend() {
  const appRoot = getAppRoot()
  const backendDir = path.join(appRoot, 'apps', 'backend')
  const env = {
    ...process.env,
    PYTHONPATH: appRoot,
    HTTP_PROXY: '',
    HTTPS_PROXY: '',
    http_proxy: '',
    https_proxy: '',
  }

  backendProcess = spawn('python', ['-m', 'app.main'], {
    cwd: backendDir,
    stdio: ['ignore', 'pipe', 'pipe'],
    env,
  })

  backendProcess.stdout.on('data', (d) => {
    const text = d.toString()
    process.stdout.write(`[backend] ${text}`)

    const lines = text.split('\n')
    for (const line of lines) {
      if (line.startsWith('[PROGRESS]')) {
        const parts = line.replace('[PROGRESS] ', '').split('|')
        if (parts.length >= 3) {
          sendStatus({
            state: 'loading',
            message: parts[2],
            progress: parseFloat(parts[0]) || 0,
          })
        }
      }
    }
  })

  backendProcess.stderr.on('data', (d) => process.stderr.write(`[backend] ${d}`))

  backendProcess.on('error', (err) => {
    console.error('[backend] Failed to start:', err.message)
    sendStatus({ state: 'error', message: err.message })
    dialog.showErrorBox(
      'Python Not Found',
      'Could not launch the Python backend.\n\n' +
      'Make sure Python 3.12+ is installed and in your PATH.\n' +
      'Install from: https://www.python.org/downloads/\n\n' +
      err.message
    )
  })

  backendProcess.on('exit', (code) => {
    console.log(`[backend] Exited with code ${code}`)
    backendProcess = null
    sendStatus({ state: 'error', message: `Process exited (code ${code})` })
  })
}

function pollBackend() {
  let attempt = 0
  healthInterval = setInterval(() => {
    attempt++
    const req = http.get('http://127.0.0.1:8000/health', (res) => {
      let body = ''
      res.on('data', (c) => (body += c))
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            const data = JSON.parse(body)
            if (data.status === 'ready') {
              sendStatus({ state: 'ready' })
              clearInterval(healthInterval)
              healthInterval = null
            } else {
              sendStatus({
                state: 'loading',
                message: data.message || 'Starting backend...',
                progress: data.progress || 0,
              })
            }
          } catch {
            sendStatus({ state: 'ready' })
            clearInterval(healthInterval)
            healthInterval = null
          }
        }
      })
    })
    req.on('error', () => {
      if (attempt > 120) {
        sendStatus({ state: 'error', message: 'Backend did not start in time' })
        clearInterval(healthInterval)
        healthInterval = null
      }
    })
    req.setTimeout(2000, () => { req.destroy() })
  }, 1000)
}

function stopBackend() {
  if (healthInterval) clearInterval(healthInterval)
  if (backendProcess) {
    backendProcess.kill('SIGTERM')
    setTimeout(() => {
      if (backendProcess) backendProcess.kill('SIGKILL')
    }, 3000)
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    resizable: true,
    center: true,
    backgroundColor: '#0f0f13',
    show: false,
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => mainWindow.show())
  mainWindow.on('closed', () => { mainWindow = null })
}

async function reloadSystemProxy() {
  try {
    await session.defaultSession.setProxy({ mode: 'system' })
    await session.defaultSession.closeAllConnections()
    console.log('Operating system proxy configuration reloaded.')
  } catch (err) {
    console.error('Failed to apply operating system proxy configuration:', err.message)
  }
}

app.whenReady().then(async () => {
  try {
    console.log('Using operating system proxy configuration.')
    await session.defaultSession.setProxy({ mode: 'system' })
    await session.defaultSession.closeAllConnections()
    console.log('Operating system proxy configuration applied.')
  } catch (err) {
    console.error('Failed to apply operating system proxy configuration:', err.message)
  }

  session.defaultSession.setPermissionRequestHandler(
    (webContents, permission, callback) => {
      if (permission === 'media') {
        callback(true)
      } else {
        callback(false)
      }
    }
  )

  createWindow()
  startBackend()
  pollBackend()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('will-quit', () => stopBackend())
