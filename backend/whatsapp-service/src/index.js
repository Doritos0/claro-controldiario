const express = require('express');
const fs = require('fs');
const path = require('path');
const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');

const PORT = Number(process.env.WHATSAPP_SERVICE_PORT || 3020);
const BASE_DIR = path.resolve(__dirname, '..');
const SESSION_DIR = path.join(BASE_DIR, 'sessions');
const DEFAULT_DOWNLOADS_DIR = path.join(BASE_DIR, 'downloads');
const FETCH_BATCH_SIZE = Number(process.env.WA_FETCH_BATCH_SIZE || 200);
const FETCH_MAX_BATCHES = Number(process.env.WA_FETCH_MAX_BATCHES || 60);
const FETCH_MAX_MS = Number(process.env.WA_FETCH_MAX_MS || 120000);
const MEDIA_DOWNLOAD_TIMEOUT_MS = Number(process.env.WA_MEDIA_DOWNLOAD_TIMEOUT_MS || 20000);

fs.mkdirSync(SESSION_DIR, { recursive: true });
fs.mkdirSync(DEFAULT_DOWNLOADS_DIR, { recursive: true });

const app = express();
app.use(express.json());

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: SESSION_DIR, clientId: 'main' }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }
});

let ready = false;

client.on('qr', (qr) => {
  console.log('\n[WhatsApp] Escanea este QR para iniciar sesión:');
  qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
  console.log('[WhatsApp] Sesión autenticada.');
});

client.on('ready', () => {
  ready = true;
  console.log('[WhatsApp] Cliente listo.');
});

client.on('auth_failure', (msg) => {
  ready = false;
  console.error('[WhatsApp] Fallo de autenticación:', msg);
});

client.on('disconnected', (reason) => {
  ready = false;
  console.warn('[WhatsApp] Cliente desconectado:', reason);
});

function sanitizeFileName(value) {
  return String(value || 'desconocido')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9_-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .toLowerCase();
}

function parseDateInput(dateStr) {
  // Espera dd/mm/yy
  const match = /^(\d{2})\/(\d{2})\/(\d{2})$/.exec(String(dateStr || '').trim());
  if (!match) {
    throw new Error('Formato de fecha inválido. Usa dd/mm/yy, por ejemplo 05/03/26.');
  }

  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = 2000 + Number(match[3]);

  const start = new Date(year, month - 1, day, 0, 0, 0, 0);
  const end = new Date(year, month - 1, day, 23, 59, 59, 999);

  if (Number.isNaN(start.getTime())) {
    throw new Error('Fecha inválida.');
  }

  return { start, end, folderName: `${match[1]}-${match[2]}-${match[3]}` };
}

function withTimeout(promise, timeoutMs, errorMessage) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(errorMessage)), timeoutMs))
  ]);
}

async function findGroupChatByName(groupName) {
  const chats = await client.getChats();
  const normalizedTarget = groupName.trim().toLowerCase();

  return chats.find(
    (chat) => chat.isGroup && chat.name && chat.name.trim().toLowerCase() === normalizedTarget
  );
}

async function fetchMessagesForDate(chat, start, end) {
  const messages = [];
  const seenMessageIds = new Set();

  let reachedOlderThanDay = false;
  const startedAt = Date.now();
  let batchNumber = 0;
  let beforeMessageId;

  while (!reachedOlderThanDay && batchNumber < FETCH_MAX_BATCHES) {
    if (Date.now() - startedAt > FETCH_MAX_MS) {
      console.warn('[WhatsApp] fetchMessagesForDate alcanzó timeout global.');
      break;
    }

    const options = { limit: FETCH_BATCH_SIZE };
    if (beforeMessageId) {
      options.before = beforeMessageId;
    }

    batchNumber += 1;
    const batch = await chat.fetchMessages(options);
    if (!batch.length) break;

    const firstId = batch[0]?.id?._serialized || 'n/a';
    const lastId = batch[batch.length - 1]?.id?._serialized || 'n/a';
    console.log(`[WhatsApp] Lote ${batchNumber}: ${batch.length} mensajes (first=${firstId}, last=${lastId})`);

    if (beforeMessageId && lastId === beforeMessageId) {
      console.warn('[WhatsApp] Cursor no avanzó; se detiene para evitar repetición de lotes.');
      break;
    }

    for (const msg of batch) {
      const messageId = msg.id?._serialized;
      if (!messageId || seenMessageIds.has(messageId)) {
        continue;
      }
      seenMessageIds.add(messageId);

      const msgDate = new Date(msg.timestamp * 1000);
      if (msgDate < start) {
        reachedOlderThanDay = true;
        continue;
      }
      if (msgDate >= start && msgDate <= end) {
        messages.push(msg);
      }
    }

    beforeMessageId = lastId !== 'n/a' ? lastId : undefined;
  }

  if (batchNumber >= FETCH_MAX_BATCHES) {
    console.warn('[WhatsApp] fetchMessagesForDate alcanzó el máximo de lotes configurado.');
  }

  return messages;
}

async function downloadImagesFromMessages(messages, outputDir, datePrefix) {
  let saved = 0;
  const downloadedMessageIds = new Set();

  for (const msg of messages) {
    const messageId = msg.id?._serialized;
    if (!messageId || downloadedMessageIds.has(messageId)) continue;
    downloadedMessageIds.add(messageId);
    if (!msg.hasMedia) continue;
    if (msg.type !== 'image') continue;

    const media = await withTimeout(
      msg.downloadMedia(),
      MEDIA_DOWNLOAD_TIMEOUT_MS,
      `Timeout descargando media para mensaje ${msg.id?._serialized || 'unknown'}`
    );
    if (!media) continue;

    const senderRaw = msg._data?.notifyName || msg.author || msg.from || 'desconocido';
    const sender = sanitizeFileName(senderRaw);
    const extension = (media.mimetype && media.mimetype.split('/')[1]) || 'jpg';

    let fileName = `${datePrefix}_${sender}.${extension}`;
    let filePath = path.join(outputDir, fileName);
    let i = 1;

    while (fs.existsSync(filePath)) {
      fileName = `${datePrefix}_${sender}_${String(i).padStart(2, '0')}.${extension}`;
      filePath = path.join(outputDir, fileName);
      i += 1;
    }

    fs.writeFileSync(filePath, media.data, { encoding: 'base64' });
    saved += 1;
  }

  return saved;
}

app.get('/health', (_req, res) => {
  res.json({ ok: true, whatsappReady: ready });
});

app.post('/whatsapp/download-images', async (req, res) => {
  try {
    if (!ready) {
      return res.status(503).json({
        ok: false,
        message: 'WhatsApp aún no está listo. Escanea el QR y espera estado ready.'
      });
    }

    const { groupName, date, outputBaseDir } = req.body || {};

    if (!groupName || !date) {
      return res.status(400).json({
        ok: false,
        message: 'Debes enviar groupName y date (dd/mm/yy).'
      });
    }

    const { start, end, folderName } = parseDateInput(date);
    const outputRoot = path.resolve(outputBaseDir || DEFAULT_DOWNLOADS_DIR);
    const outputDir = path.join(outputRoot, folderName);
    fs.mkdirSync(outputDir, { recursive: true });

    const chat = await findGroupChatByName(groupName);
    if (!chat) {
      return res.status(404).json({ ok: false, message: `No se encontró el grupo '${groupName}'.` });
    }

    const dayMessages = await Promise.race([
      fetchMessagesForDate(chat, start, end),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout buscando mensajes en el chat.')), FETCH_MAX_MS + 10000)
      )
    ]);
    const saved = await downloadImagesFromMessages(dayMessages, outputDir, folderName);

    return res.json({
      ok: true,
      groupName,
      date,
      outputDir,
      totalMessagesInDate: dayMessages.length,
      totalImagesSaved: saved
    });
  } catch (error) {
    console.error(error);
    return res.status(500).json({ ok: false, message: error.message || 'Error interno' });
  }
});

app.listen(PORT, () => {
  console.log(`[service] escuchando en http://localhost:${PORT}`);
});

client.initialize();
