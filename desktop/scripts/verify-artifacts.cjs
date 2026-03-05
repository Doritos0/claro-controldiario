const fs = require('fs');
const path = require('path');

const requiredPaths = [
  path.resolve(__dirname, '../../frontend/dist/index.html'),
  path.resolve(__dirname, '../../release/backend/backend.exe'),
  path.resolve(__dirname, '../../release/whatsapp-service/whatsapp-service.exe'),
];

const missing = requiredPaths.filter((file) => !fs.existsSync(file));
if (missing.length > 0) {
  console.error('Faltan artefactos para empaquetar Electron:');
  for (const file of missing) console.error(` - ${file}`);
  process.exit(1);
}

console.log('Artefactos listos para electron-builder');
