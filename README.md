# Document AI Pipeline with Azure Document Intelligence

Aplicación Python para subir un PDF, extraer solo la primera página, convertirla en imagen y clasificar el tipo documental con un Custom Classification Model de Azure AI Document Intelligence.

## Flujo

1. El usuario sube un PDF desde Streamlit.
2. FastAPI guarda temporalmente el archivo.
3. Se extrae la primera página y se convierte a imagen.
4. El clasificador custom de Azure Document Intelligence determina el tipo documental.
5. El backend devuelve la etiqueta detectada, su confianza y el tiempo de procesamiento.
6. El frontend muestra el resultado y permite descargarlo en JSON.

## Tipos documentales incluidos

Los tipos dependen de las clases que tengas entrenadas en tu Custom Classification Model, por ejemplo:

- `Formato de cumplimiento`
- `Entrada de mercancía`
- `Orden de compra A`
- `Orden de compra B`

## Estructura

```text
document-ai-pipeline/
  app/
    backend/
    classifiers/
    config/
    frontend/
    repositories/
    schemas/
    services/
    tests/
    utils/
  storage/
    logs/
    tmp/
  .env.example
  main.py
  requirements.txt
  README.md
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Completa en `.env`:

- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
- `AZURE_DOCUMENT_INTELLIGENCE_KEY`
- `AZURE_DOCUMENT_INTELLIGENCE_CLASSIFIER_ID`

## Ejecutar backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Ejecutar frontend

```bash
streamlit run app/frontend/streamlit_app.py
```

## Uso por API

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@/ruta/al/documento.pdf"
```

Respuesta esperada:

```json
{
  "id": "uuid",
  "document_type": "Orden de compra A",
  "confidence": 0.97,
  "processing_time_ms": 1850,
  "created_at": "2026-07-28T12:00:00Z"
}
```

## Configuración del clasificador en Azure

Este proyecto asume que ya tienes en Document Intelligence Studio:

- Un `classifier` custom entrenado para tus tipos documentales.

La clasificación usa el SDK `begin_classify_document(...)` sobre la imagen de la primera página.

## Pruebas

```bash
pytest app/tests
```

## Limitaciones actuales

- La persistencia es en memoria; si reinicia la API, se pierde el historial.
- La clasificación usa la imagen de la primera página.
- El sistema solo clasifica; no extrae campos del documento.
- La etiqueta devuelta depende exactamente de las clases configuradas en tu Custom Classification Model.
