const express = require('express');
const cors = require('cors');
const WhatsAppDownloader = require('./extractor');
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');
const QRCode = require('qrcode');

const app = express();

app.use(cors({
  origin: 'http://localhost:5173',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Mi API de Node (WhatsApp Extractor)',
      version: '1.0.0',
      description: 'Servicio para extraer fotos de grupos de WhatsApp'
    },
    servers: [
      {
        url: 'http://localhost:3000',
      },
    ],
  },
  apis: [__filename],
};

const swaggerSpec = swaggerJsdoc(options);

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

app.get('/openapi.json', (req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(swaggerSpec);
});

const downloader = new WhatsAppDownloader();

/**
 * @openapi
 * /iniciar-sesion:
 *   post:
 *     summary: Inicializa WhatsApp y devuelve el QR si aún no está autenticado
 *     responses:
 *       200:
 *         description: Estado de sesión de WhatsApp
 */
app.post('/iniciar-sesion', async (_req, res) => {
  try {
    await downloader.iniciar();
    const state = downloader.getSessionState();
    const qrImage = state.qr ? await QRCode.toDataURL(state.qr) : null;

    res.json({
      status: state.status,
      ready: state.ready,
      qr: qrImage,
      error: state.error
    });
  } catch (error) {
    res.status(500).json({
      status: 'failed',
      error: error.message
    });
  }
});

/**
 * @openapi
 * /estado-sesion:
 *   get:
 *     summary: Devuelve el estado actual de la sesión de WhatsApp
 *     responses:
 *       200:
 *         description: Estado actual
 */
app.get('/estado-sesion', async (_req, res) => {
  const state = downloader.getSessionState();
  const qrImage = state.qr ? await QRCode.toDataURL(state.qr) : null;

  res.json({
    status: state.status,
    ready: state.ready,
    qr: qrImage,
    error: state.error
  });
});

/**
 * @openapi
 * /descargar:
 *   post:
 *     summary: Descargar fotos de un grupo por fecha
 *     operationId: descargarFotos
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - nombreGrupo
 *               - fecha
 *             properties:
 *               nombreGrupo:
 *                 type: string
 *                 example: "Reportes Diarios"
 *               fecha:
 *                 type: string
 *                 example: "09/03/2026"
 *     responses:
 *       200:
 *         description: Proceso finalizado
 *       400:
 *         description: Parámetros inválidos
 *       500:
 *         description: Error en el servidor
 */
app.post('/descargar', async (req, res) => {
  const { nombreGrupo, fecha } = req.body;

  if (!nombreGrupo || !fecha) {
    return res.status(400).json({ error: 'Faltan parametros' });
  }

  if (!downloader.estaListo()) {
    return res.status(503).json({ error: 'WhatsApp aún no está listo' });
  }

  try {
    const resultado = await downloader.descargarFotosPorFecha(nombreGrupo, fecha);

    res.json({
      mensaje: `Proceso de descarga finalizado para grupo ${nombreGrupo}`,
      fecha,
      totalImagenes: resultado.totalImagenes,
      carpeta: resultado.carpeta
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({
      error: 'Error al procesar la descarga',
      detalle: error.message
    });
  }
});

app.get('/health', (_req, res) => {
  res.json({ ok: true, whatsappReady: downloader.estaListo() });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Servidor de Node listo en http://localhost:${PORT}`);
  console.log(`Documentación en http://localhost:${PORT}/docs`);
});