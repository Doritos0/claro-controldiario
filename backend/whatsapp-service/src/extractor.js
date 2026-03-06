const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const fs = require('fs');
const path = require('path');

class WhatsAppDownloader {
    constructor() {
        this.client = new Client({
            authStrategy: new LocalAuth({ dataPath: './sessions' }),
            puppeteer: { headless: true } 
        });
    }

    async iniciar() {
        return new Promise((resolve) => {
            this.client.on('qr', qr => qrcode.generate(qr, { small: true }));
            this.client.on('ready', () => {
                console.log('Conexión establecida');
                resolve();
            });
            this.client.initialize();
        });
    }

    /**
     * @param {string} nombreGrupo - Nombre exacto del grupo
     * @param {string} fechaStr - Formato "DD/MM/YYYY"
     */
    async descargarFotosPorFecha(nombreGrupo, fechaStr) {
        // 1. Convertir fecha a rango de inicio y fin de día
        const [dia, mes, año] = fechaStr.split('/').map(Number);
        const inicioDia = new Date(año, mes - 1, dia, 0, 0, 0).getTime() / 1000;
        const finDia = new Date(año, mes - 1, dia, 23, 59, 59).getTime() / 1000;

        // 2. Buscar el chat
        const chats = await this.client.getChats();
        const grupo = chats.find(c => c.isGroup && c.name === nombreGrupo);
        
        if (!grupo) throw new Error(`Grupo "${nombreGrupo}" no encontrado.`);

        console.log(`Buscando fotos en "${nombreGrupo}" para el ${fechaStr}...`);

        // 3. Cargar mensajes (Traemos un lote grande para asegurar cubrir el día)
        const mensajes = await grupo.fetchMessages({ limit: 500 });
        
        // 4. Filtrar y Descargar
        let contador = 0;
        const nombreCarpeta = fechaStr.replace(/\//g, '-');
        const carpeta = `./descargas/${nombreCarpeta}`;
        if (!fs.existsSync(carpeta)) fs.mkdirSync(carpeta, { recursive: true });

        for (const msg of mensajes) {
            // ¿Está dentro del día y tiene imagen?
            if (msg.timestamp >= inicioDia && msg.timestamp <= finDia && msg.hasMedia && msg.type === 'image') {
                const media = await msg.downloadMedia();
                if (media) {
                    const extension = media.mimetype.split('/')[1];

                    const autor = msg.author || msg.from;
                    const nroTelefono = autor.split('@')[0];
                    const idMensaje = msg.id.id

                    const fileName = `${nombreCarpeta}_${nroTelefono}_${idMensaje}.${extension}`;
                    fs.writeFileSync(path.join(carpeta, fileName), media.data, 'base64');
                    contador++;
                }
            }
        }

        console.log(`Proceso finalizado. Se guardaron ${contador} imágenes en: ${carpeta}`);
    }
}

module.exports = WhatsAppDownloader;