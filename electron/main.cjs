const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

let mainWindow;
let spawnedProcesses = [];

function checkPort(port) {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/`, (res) => resolve(true));
    req.on('error', () => resolve(false));
    req.setTimeout(500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function ensureServices() {
  const rootDir = path.join(__dirname, '..');
  const pythonExe = path.join(rootDir, 'venv', 'Scripts', 'python.exe');

  const pyRunning = await checkPort(8000);
  if (!pyRunning) {
    console.log('[Electron] Starting FastAPI backend on :8000...');
    const py = spawn(pythonExe, ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '8000'], {
      cwd: rootDir,
      stdio: 'ignore',
      windowsHide: true
    });
    spawnedProcesses.push(py);
  }

  const crmRunning = await checkPort(3002);
  if (!crmRunning) {
    console.log('[Electron] Starting CRM Node backend on :3002...');
    const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
    const crm = spawn(npmCmd, ['run', 'server'], {
      cwd: path.join(rootDir, 'credit-crm'),
      stdio: 'ignore',
      windowsHide: true
    });
    spawnedProcesses.push(crm);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1080,
    minHeight: 720,
    title: "TrueBuild Suite — Desktop Edition (Sumthin3lse Global)",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs')
    },
    backgroundColor: '#090d16',
    autoHideMenuBar: true
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'desktop_shell.html'));

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function cleanup() {
  for (const proc of spawnedProcesses) {
    try {
      proc.kill();
    } catch (e) {}
  }
}

app.whenReady().then(async () => {
  await ensureServices();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  cleanup();
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', () => {
  cleanup();
});
