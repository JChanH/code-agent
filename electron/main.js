const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { PythonManager } = require('./python-manager');

let mainWindow = null;
const pythonManager = new PythonManager();

const isDev = !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hiddenInset',
    title: 'Code Agent',
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── IPC Handlers ────────────────────────────

ipcMain.handle('dialog:openDirectory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Select Project Directory',
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('dialog:openFile', async (_event, filters) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: filters || [{ name: 'All Files', extensions: ['*'] }],
    title: 'Select File',
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('app:getBackendUrl', () => {
  return 'http://localhost:8000';
});

ipcMain.handle('app:getWsUrl', () => {
  return 'ws://localhost:8000';
});

// ── App Lifecycle ───────────────────────────

app.on('ready', async () => {
  // Start Python backend
  try {
    await pythonManager.start();
    console.log('[Electron] Python backend started');
  } catch (err) {
    console.error('[Electron] Failed to start Python backend:', err.message);
  }

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', async () => {
  await pythonManager.stop();
});
