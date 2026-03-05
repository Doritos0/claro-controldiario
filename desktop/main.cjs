const { app, BrowserWindow, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const isDev = process.env.ELECTRON_DEV === '1';
const managedProcesses = [];

function spawnManaged(command, args, options) {
  const child = spawn(command, args, {
    stdio: 'pipe',
    windowsHide: true,
    ...options,
  });

  child.stdout.on('data', (chunk) => console.log(`[${path.basename(command)}] ${chunk}`));
  child.stderr.on('data', (chunk) => console.error(`[${path.basename(command)}] ${chunk}`));
  child.on('exit', (code) => console.log(`[${path.basename(command)}] exit code ${code}`));
  managedProcesses.push(child);
  return child;
}

function startServices() {
  if (isDev) {
    spawnManaged('python', ['-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', '8000'], {
      cwd: path.resolve(__dirname, '../backend'),
    });
    spawnManaged('npm', ['start'], {
      cwd: path.resolve(__dirname, '../backend/whatsapp-service'),
      shell: true,
    });
    return;
  }

  const resources = process.resourcesPath;
  const backendExe = path.join(resources, 'backend', 'backend.exe');
  const whatsappExe = path.join(resources, 'whatsapp-service', 'whatsapp-service.exe');

  spawnManaged(backendExe, [], {});
  spawnManaged(whatsappExe, [], {});
}

function getFrontendEntry() {
  if (isDev) {
    return { type: 'url', value: 'http://127.0.0.1:5173' };
  }
  return {
    type: 'file',
    value: path.join(process.resourcesPath, 'frontend', 'index.html'),
  };
}

async function createWindow() {
  const win = new BrowserWindow({
    width: 1360,
    height: 880,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const target = getFrontendEntry();
  if (target.type === 'url') {
    await win.loadURL(target.value);
  } else {
    await win.loadFile(target.value);
  }
}

app.whenReady().then(async () => {
  try {
    startServices();
    await createWindow();
  } catch (error) {
    dialog.showErrorBox('Error iniciando aplicación', String(error));
    app.quit();
  }

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createWindow();
    }
  });
});

app.on('before-quit', () => {
  for (const child of managedProcesses) {
    if (!child.killed) child.kill('SIGTERM');
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
