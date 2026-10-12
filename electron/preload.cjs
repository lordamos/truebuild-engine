const { contextBridge, shell } = require('electron');

contextBridge.exposeInMainWorld('electronApi', {
  openExternal: (url) => shell.openExternal(url)
});
