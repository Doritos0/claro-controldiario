const express = require('express');
const WhatsAppDownloader = require('./extractor');
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const app = express();
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
  apis: ['./src/index.js'],
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
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 mensaje:
 *                   type: string
 *                 fecha:
 *                   type: string
 *       400:
 *         description: Parámetros inválidos
 *       500:
 *         description: Error en el servidor
 */
app.post('/descargar', async (req, res) => {
  const { nombreGrupo, fecha } = req.body;

  if (!nombreGrupo || !fecha) {
    return res.status(400).json({ error: "Faltan parametros" });
  }

  try {
    await downloader.descargarFotosPorFecha(nombreGrupo, fecha);
    res.json({
      mensaje: `Proceso de descarga finalizado para grupo ${nombreGrupo}`,
      fecha: fecha
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({
      error: "Error al procesar la descarga",
      detalle: error.message
    });
  }
});

downloader.iniciar()
  .then(() => {
    const PORT = 3000;
    app.listen(PORT, () => {
      console.log(`Servidor de Node listo en http://localhost:${PORT}`);
    });
  })
  .catch(err => console.error(err));