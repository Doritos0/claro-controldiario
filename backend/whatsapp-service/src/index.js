const express = require('express');
const WhatsAppDownloader = require('./extractor');

const app = express()

app.use(express.json())

const downloader = new WhatsAppDownloader()

downloader.iniciar()
    .then(() => {
        console.log("Iniciando WhatsApp");
        const PORT = 3000;
        app.listen(PORT, () => {
            console.log(`Servidor en http://localhost:${PORT}`)
        });
    })
    .catch(err => {
        console.error("Error iniciando WhatsApp: ",err);
    });

//RUTA API
app.post('/descargar', async(req, res) => {
    const { nombreGrupo, fecha } = req.body;

    if (!nombreGrupo || !fecha) {
        return res.status(400).json({
            error: "Faltan parametros"
        })
    }

    try {
        await downloader.descargarFotosPorFecha(nombreGrupo, fecha);
        res.json({
            mensaje: `Proceso de descarga iniciado para grupo ${nombreGrupo}`,
            fecha: fecha
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({
            error: "Error al procesar la descarga",
            detalle: error.message
        })
    }
});