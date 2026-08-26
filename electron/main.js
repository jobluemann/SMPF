const { app, BrowserWindow, shell, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const isDev = process.env.NODE_ENV === 'development';

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    title: 'SMPF',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false
    }
  });

  // Load the bundled web UI from the packaged www folder.
  const uiPath = path.join(__dirname, 'www', 'index.html');
  win.loadFile(uiPath);

  // Open external links in the system browser.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

function getKeysPath() {
  return path.join(app.getPath('userData'), 'keys.json');
}

app.whenReady().then(() => {
  ipcMain.handle('get-user-data-path', () => app.getPath('userData'));
  ipcMain.handle('read-config-file', () => {
    const file = getKeysPath();
    try {
      if (!fs.existsSync(file)) return null;
      return JSON.parse(fs.readFileSync(file, 'utf8'));
    } catch (e) {
      console.error('Failed to read keys file:', e.message);
      return null;
    }
  });
  ipcMain.handle('write-config-file', (_event, data) => {
    const file = getKeysPath();
    try {
      fs.writeFileSync(file, JSON.stringify(data, null, 2));
      return true;
    } catch (e) {
      console.error('Failed to write keys file:', e.message);
      return false;
    }
  });

  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
