const { contextBridge } = require('electron');

// Expose a minimal safe API if needed. The web UI runs as a normal
// Chromium page, so Web Speech API (TTS + STT) is available natively.
contextBridge.exposeInMainWorld('kimiNative', {
  platform: process.platform
});
