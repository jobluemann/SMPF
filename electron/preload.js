const { contextBridge, ipcRenderer } = require('electron');

// Expose a minimal safe API to the renderer so the app can read/write
// API keys from a local JSON file in the app's user-data directory.
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  getUserDataPath: () => ipcRenderer.invoke('get-user-data-path'),
  readConfig: () => ipcRenderer.invoke('read-config-file'),
  writeConfig: (data) => ipcRenderer.invoke('write-config-file', data)
});
