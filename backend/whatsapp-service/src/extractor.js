const { Client, LocalAuth } = require('whatsapp-web.js');
const fs = require('fs');
const path = require('path');

class WhatsAppDownloader {
  constructor() {
    this.client = new Client({
      authStrategy: new LocalAuth({ dataPath: path.join(__dirname, '..', 'sessions') }),
      puppeteer: { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox'] },
    });

    this.state = {
      status: 'idle',
      qr: null,
      error: null,
    };
    this.initialized = false;
    this._bindEvents();
  }

  _bindEvents() {
    this.client.on('qr', (qr) => {
      this.state = { status: 'qr', qr, error: null };
    });
    this.client.on('authenticated', () => {
      this.state = { status: 'authenticated', qr: null, error: null };
    });
    this.client.on('ready', () => {
      this.state = { status: 'ready', qr: null, error: null };
    });
    this.client.on('auth_failure', (message) => {
      this.state = { status: 'failed', qr: null, error: message || 'Auth failure' };
    });
    this.client.on('disconnected', (reason) => {
      this.state = { status: 'disconnected', qr: null, error: reason || 'Disconnected' };
      this.initialized = false;
    });
  }

  async iniciar() {
    if (this.initialized) {
      return this.state;
    }
    this.initialized = true;
    this.state = { status: 'starting', qr: null, error: null };
    this.client.initialize();
    return this.state;
  }

  getSessionState() {
    return this.state;
  }

  async descargarFotosPorFecha(nombreGrupo, fechaStr) {
    if (this.state.status !== 'ready' && this.state.status !== 'authenticated') {
      throw new Error('WhatsApp no está autenticado. Inicia sesión primero.');
    }

    const [dia, mes, anio] = fechaStr.split('/').map(Number);
    const anioReal = anio < 100 ? 2000 + anio : anio;
    const inicioDia = new Date(anioReal, mes - 1, dia, 0, 0, 0).getTime() / 1000;
    const finDia = new Date(anioReal, mes - 1, dia, 23, 59, 59).getTime() / 1000;

    const chats = await this.client.getChats();
    const grupo = chats.find((c) => c.isGroup && c.name === nombreGrupo);
    if (!grupo) {
      throw new Error(`Grupo "${nombreGrupo}" no encontrado.`);
    }

    const mensajes = await grupo.fetchMessages({ limit: 1000 });

    const nombreCarpeta = fechaStr.replace(/\//g, '-');
    const carpeta = path.join(__dirname, 'descargas', nombreCarpeta);
    fs.mkdirSync(carpeta, { recursive: true });

    let contador = 0;
    for (const msg of mensajes) {
      if (msg.timestamp >= inicioDia && msg.timestamp <= finDia && msg.hasMedia && msg.type === 'image') {
        const media = await msg.downloadMedia();
        if (!media) continue;
        const extension = (media.mimetype || 'image/jpeg').split('/')[1] || 'jpeg';
        const autor = msg.author || msg.from || 'desconocido@c.us';
        const nroTelefono = autor.split('@')[0];
        const idMensaje = msg.id.id;
        const fileName = `${nombreCarpeta}_${nroTelefono}_${idMensaje}.${extension}`;
        fs.writeFileSync(path.join(carpeta, fileName), media.data, 'base64');
        contador += 1;
      }
    }

    return { carpeta, totalImagenes: contador };
  }
}

module.exports = { WhatsAppDownloader };
