const express = require('express');
const cors = require('cors');
const QRCode = require('qrcode');
const { WhatsAppDownloader } = require('./extractor');

const app = express();
const port = process.env.PORT || 3100;
const downloader = new WhatsAppDownloader();

app.use(cors());
app.use(express.json());

app.post('/iniciar-session', async (_req, res) => {
  try {
    await downloader.iniciar();
    const state = downloader.getSessionState();
    const qrImage = state.qr ? await QRCode.toDataURL(state.qr) : null;
    res.json({ status: state.status, qr: qrImage, error: state.error });
  } catch (error) {
    res.status(500).json({ status: 'failed', error: error.message });
  }
});

app.get('/iniciar-session', async (_req, res) => {
  const state = downloader.getSessionState();
  const qrImage = state.qr ? await QRCode.toDataURL(state.qr) : null;
  res.json({ status: state.status, qr: qrImage, error: state.error });
});

app.post('/descargar-imagenes', async (req, res) => {
  try {
    const { nombre_grupo, fecha } = req.body;
    if (!nombre_grupo || !fecha) {
      return res.status(400).json({ error: 'nombre_grupo y fecha son obligatorios' });
    }

    const resultado = await downloader.descargarFotosPorFecha(nombre_grupo, fecha);
    return res.json({ ok: true, ...resultado });
  } catch (error) {
    return res.status(500).json({ ok: false, error: error.message });
  }
});

app.listen(port, () => {
  console.log(`whatsapp-service API en http://localhost:${port}`);
});
