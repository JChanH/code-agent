const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Dialog
  openDirectory: () => ipcRenderer.invoke('dialog:openDirectory'),
  openFile: (filters) => ipcRenderer.invoke('dialog:openFile', filters),

  // App config
  getBackendUrl: () => ipcRenderer.invoke('app:getBackendUrl'),
  getWsUrl: () => ipcRenderer.invoke('app:getWsUrl'),
});
