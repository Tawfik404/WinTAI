const { app, BrowserWindow, dialog, session } = require('electron')
const path = require('path')
const fs = require('fs')
const { spawn } = require('child_process')
const http = require('http')

if (!process.env.GOOGLE_API_KEY && process.env.WINTAI_GOOGLE_API_KEY) {
  process.env.GOOGLE_API_KEY = process.env.WINTAI_GOOGLE_API_KEY
}

let mainWindow
let backendProcess = null
let healthInterval = null
let frontendServer = null

const MIME = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.json': 'application/json',
}

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

// ------------------------------------------------------------------
// Backend
// ------------------------------------------------------------------

function startBackend() {
  const appRoot = getAppRoot()
  const backendDir = path.join(appRoot, 'apps', 'backend')
  const env = {
    ...process.env,
    PYTHONPATH: appRoot,
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

// ------------------------------------------------------------------
// Frontend HTTP server (production)
// SpeechRecognition requires an HTTP(S) origin — file:// won't work.
// ------------------------------------------------------------------

function createFrontendServer() {
  return new Promise((resolve, reject) => {
    const distDir = path.join(__dirname, '../dist')

    const server = http.createServer((req, res) => {
      // Serve static files
      let filePath = path.join(distDir, req.url === '/' ? 'index.html' : req.url.split('?')[0])

      // SPA fallback — serve index.html for any unrecognised path
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(distDir, 'index.html')
      }

      const ext = path.extname(filePath)
      const contentType = MIME[ext] || 'application/octet-stream'

      fs.readFile(filePath, (err, data) => {
        if (err) {
          res.writeHead(404)
          res.end('Not found')
          return
        }
        res.writeHead(200, { 'Content-Type': contentType })
        res.end(data)
      })
    })

    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port
      console.log(`[frontend] Serving dist on http://127.0.0.1:${port}`)
      frontendServer = server
      resolve(port)
    })
    server.on('error', reject)
  })
}

function stopFrontendServer() {
  if (frontendServer) {
    frontendServer.close()
    frontendServer = null
  }
}

// ------------------------------------------------------------------
// Window
// ------------------------------------------------------------------

async function createWindow() {
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
    const port = await createFrontendServer()
    mainWindow.loadURL(`http://127.0.0.1:${port}`)
  }

  mainWindow.once('ready-to-show', () => mainWindow.show())
  mainWindow.on('closed', () => { mainWindow = null })
}

// ------------------------------------------------------------------
// App lifecycle
// ------------------------------------------------------------------

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler(
    (webContents, permission, callback) => {
      if (permission === 'media') {
        callback(true)
      } else {
        callback(false)
      }
    }
  )

  await createWindow()
  startBackend()

  pollBackend()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('will-quit', () => {
  stopBackend()
  stopFrontendServer()
})

