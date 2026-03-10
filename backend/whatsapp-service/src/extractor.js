const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

class WhatsAppDownloader {
  constructor() {
    this.ready = false;
    this.qr = null;
    this.error = null;
    this.status = 'idle';
    this.initializing = false;

    this.client = new Client({
      authStrategy: new LocalAuth({ dataPath: './sessions' }),
      puppeteer: { headless: true }
    });

    this.eventsRegistered = false;
  }

  registerEvents() {
    if (this.eventsRegistered) return;
    this.eventsRegistered = true;

    this.client.on('qr', (qr) => {
      this.qr = qr;
      this.status = 'qr_pending';
      this.error = null;
      this.initializing = false;
      console.log('Escanea el QR');
      qrcode.generate(qr, { small: true });
    });

    this.client.on('ready', () => {
      this.ready = true;
      this.qr = null;
      this.status = 'ready';
      this.error = null;
      this.initializing = false;
      console.log('Conexión establecida');
    });

    this.client.on('authenticated', () => {
      this.status = 'authenticated';
      this.error = null;
      console.log('Autenticado correctamente');
    });

    this.client.on('auth_failure', (msg) => {
      this.ready = false;
      this.status = 'auth_failure';
      this.error = msg;
      this.initializing = false;
      console.error(`Fallo de autenticación: ${msg}`);
    });

    this.client.on('disconnected', (reason) => {
      this.ready = false;
      this.status = 'disconnected';
      this.error = reason;
      this.initializing = false;
      console.error(`Cliente desconectado: ${reason}`);
    });
  }

  estaListo() {
    return this.ready;
  }

  getSessionState() {
    return {
      ready: this.ready,
      qr: this.qr,
      error: this.error,
      status: this.status,
      initializing: this.initializing
    };
  }

  async iniciarSesion() {
    if (this.ready || this.initializing) {
      return this.getSessionState();
    }

    this.registerEvents();
    this.initializing = true;
    this.status = 'initializing';
    this.error = null;

    this.client.initialize().catch((err) => {
      this.initializing = false;
      this.status = 'failed';
      this.error = err.message;
      console.error('Error al inicializar cliente de WhatsApp:', err.message);
    });

    return this.getSessionState();
  }

  async listarGrupos() {
    if (!this.ready) {
      throw new Error('WhatsApp aún no está listo');
    }

    const chats = await this.client.getChats();
    return chats
      .filter((chat) => chat.isGroup)
      .map((chat) => ({
        id: chat.id?._serialized,
        nombre: chat.name
      }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
  }

  async obtenerGrupo(nombreGrupo) {
    const chats = await this.client.getChats();
    return chats.find((c) => c.isGroup && c.name === nombreGrupo);
  }

  async descargarFotosPorFecha(nombreGrupo, fechaStr) {
    const partes = fechaStr.split(/[\/-]/).map(Number);
    const [dia, mes, año] = partes;

    if (partes.length !== 3 || !dia || !mes || !año) {
      throw new Error(`Fecha inválida: ${fechaStr}. Usa DD/MM/YYYY o DD-MM-YYYY`);
    }

    const inicioDia = new Date(año, mes - 1, dia, 0, 0, 0).getTime() / 1000;
    const finDia = new Date(año, mes - 1, dia, 23, 59, 59).getTime() / 1000;

    const grupo = await this.obtenerGrupo(nombreGrupo);

    if (!grupo) return { totalImagenes: 0, carpeta: 0, grupo: '', fecha: fechaStr };;

    console.log(`Buscando fotos en "${nombreGrupo}" para el ${fechaStr}...`);

    const mensajes = await grupo.fetchMessages({ limit: 500 });

    let contador = 0;
    const nombreCarpeta = fechaStr.replace(/[\/]/g, '-');
    const carpeta = `./descargas/${nombreCarpeta}`;

    if (!fs.existsSync(carpeta)) fs.mkdirSync(carpeta, { recursive: true });

    for (const msg of mensajes) {
      if (
        msg.timestamp >= inicioDia &&
        msg.timestamp <= finDia &&
        msg.hasMedia &&
        msg.type === 'image'
      ) {
        const media = await msg.downloadMedia();

        if (media) {
          const extension = media.mimetype.split('/')[1];
          const contacto = await msg.getContact();
          const celu = contacto.number;
          const idMensaje = msg.id.id;

          const fileName = `${nombreCarpeta}_${celu}_${idMensaje}.${extension}`;
          fs.writeFileSync(path.join(carpeta, fileName), media.data, 'base64');
          contador++;
        }
      }
    }

    console.log(`Proceso finalizado. Se guardaron ${contador} imágenes en: ${carpeta}`);
    return { totalImagenes: contador, carpeta, grupo: nombreGrupo, fecha: fechaStr };
  }
}

module.exports = WhatsAppDownloader;