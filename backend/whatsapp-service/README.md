# WhatsApp Media Service (`whatsapp-web.js`)

Microservicio para descargar imágenes de un grupo de WhatsApp en una fecha específica.

## Requisitos

- Node.js 18+
- Chrome/Chromium disponible (usado por `whatsapp-web.js`)

## Instalación

```bash
cd backend/whatsapp-service
npm install
```

## Ejecutar

```bash
npm start
```

Al iniciar, el servicio mostrará un QR en consola. Escanéalo con WhatsApp para autenticar.
La sesión queda persistida en `backend/whatsapp-service/sessions`.

## API

### Health

```http
GET /health
```

### Descargar imágenes por fecha

```http
POST /whatsapp/download-images
Content-Type: application/json
```

Body:

```json
{
  "groupName": "prueba rpa",
  "date": "05/03/26",
  "outputBaseDir": "./downloads"
}
```

- `groupName`: nombre exacto del grupo.
- `date`: formato `dd/mm/yy`.
- `outputBaseDir` (opcional): carpeta base donde guardar.

El servicio crea una carpeta `dd-mm-yy` y guarda allí las imágenes.

Ejemplo de respuesta:

```json
{
  "ok": true,
  "groupName": "prueba rpa",
  "date": "05/03/26",
  "outputDir": "/.../downloads/05-03-26",
  "totalMessagesInDate": 8,
  "totalImagesSaved": 5
}
```

## Troubleshooting rápido

Si una solicitud queda demorando mucho:

1. Verifica estado antes de pedir descarga:
   - `GET /health` debe devolver `whatsappReady: true`.
2. El servicio ahora tiene límites de tiempo y paginación para evitar bloqueos largos.
3. Puedes ajustar por variables de entorno:
   - `WA_FETCH_BATCH_SIZE` (default `200`)
   - `WA_FETCH_MAX_BATCHES` (default `60`)
   - `WA_FETCH_MAX_MS` (default `120000`)
   - `WA_MEDIA_DOWNLOAD_TIMEOUT_MS` (default `20000`)
