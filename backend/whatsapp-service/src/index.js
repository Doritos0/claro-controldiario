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
      version: '1.1.0',
      description: 'Servicio para autenticación y descarga de fotos de grupos de WhatsApp'
    },
    servers: [
      {
        url: 'http://localhost:3000'
      }
    ],
    components: {
      schemas: {
        SessionState: {
          type: 'object',
          properties: {
            status: { type: 'string', example: 'qr_pending' },
            ready: { type: 'boolean' },
            initializing: { type: 'boolean' },
            qr: { type: 'string', nullable: true, description: 'QR en base64 data url' },
            error: { type: 'string', nullable: true }
          }
        },
        GroupInfo: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            nombre: { type: 'string' }
          }
        },
        DescargarFotosRequest: {
          type: 'object',
          required: ['nombreGrupo', 'fecha'],
          properties: {
            nombreGrupo: { type: 'string', example: 'Reportes Diarios' },
            fecha: { type: 'string', example: '09/03/2026' }
          }
        }
      }
    }
  },
  apis: [__filename]
};

const swaggerSpec = swaggerJsdoc(options);

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

app.get('/openapi.json', (_req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.send(swaggerSpec);
});

const downloader = new WhatsAppDownloader();

const buildSessionPayload = async () => {
  const state = downloader.getSessionState();
  const qrImage = state.qr ? await QRCode.toDataURL(state.qr) : null;

  return {
    status: state.status,
    ready: state.ready,
    initializing: state.initializing,
    qr: qrImage,
    error: state.error
  };
};

/**
 * @openapi
 * /iniciar-sesion:
 *   post:
 *     summary: Inicializa la sesión de WhatsApp y devuelve estado + QR
 *     operationId: iniciarSesionWhatsapp
 *     responses:
 *       200:
 *         description: Estado de sesión de WhatsApp
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SessionState'
 */
app.post('/iniciar-sesion', async (_req, res) => {
  try {
    await downloader.iniciarSesion();
    const payload = await buildSessionPayload();
    res.json(payload);
  } catch (error) {
    res.status(500).json({
      status: 'failed',
      ready: false,
      initializing: false,
      qr: null,
      error: error.message
    });
  }
});

/**
 * @openapi
 * /estado-sesion:
 *   get:
 *     summary: Devuelve el estado actual de la sesión de WhatsApp
 *     operationId: obtenerEstadoSesionWhatsapp
 *     responses:
 *       200:
 *         description: Estado actual
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SessionState'
 */
app.get('/estado-sesion', async (_req, res) => {
  const payload = await buildSessionPayload();
  res.json(payload);
});

/**
 * @openapi
 * /grupos:
 *   get:
 *     summary: Lista los grupos disponibles de la sesión autenticada
 *     operationId: listarGruposWhatsapp
 *     responses:
 *       200:
 *         description: Lista de grupos
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/GroupInfo'
 *       503:
 *         description: WhatsApp no está listo
 */
app.get('/grupos', async (_req, res) => {
  if (!downloader.estaListo()) {
    return res.status(503).json({ error: 'WhatsApp aún no está listo' });
  }

  try {
    const grupos = await downloader.listarGrupos();
    return res.json(grupos);
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
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
 *             $ref: '#/components/schemas/DescargarFotosRequest'
 *     responses:
 *       200:
 *         description: Proceso finalizado
 *       400:
 *         description: Parámetros inválidos
 *       503:
 *         description: WhatsApp no está listo
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