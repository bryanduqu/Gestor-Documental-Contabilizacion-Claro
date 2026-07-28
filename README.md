# Document AI Pipeline with Azure Document Intelligence

Aplicación Python para subir un PDF, clasificar el tipo documental usando solo la primera página con un Custom Classification Model y luego enrutar el PDF completo al modelo de extracción de Azure correspondiente.

## Flujo

1. El usuario sube un PDF desde Streamlit.
2. FastAPI guarda temporalmente el archivo.
3. Se extrae la primera página y se convierte a imagen.
4. El clasificador custom de Azure Document Intelligence determina el tipo documental.
5. El backend resuelve el modelo de extracción configurado para esa etiqueta.
6. El PDF completo se envía al modelo de extracción correspondiente.
7. El backend devuelve el tipo detectado, la confianza, los datos extraídos y el tiempo de procesamiento.
8. El frontend muestra clasificación, JSON, tabla de campos y descarga.

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
- `AZURE_DOCUMENT_INTELLIGENCE_EXTRACTION_MODELS`

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
  "data": {
    "NumeroDocumento": "OC-1001",
    "Proveedor": "Proveedor Demo",
    "Total": 12500.45
  },
  "processing_time_ms": 1850,
  "created_at": "2026-07-28T12:00:00Z"
}
```

## Configuración en Azure

Este proyecto asume que ya tienes en Document Intelligence Studio:

- Un `classifier` custom entrenado para tus tipos documentales.
- Un modelo de extracción publicado para cada tipo documental que quieras procesar.

La clasificación usa el SDK `begin_classify_document(...)` sobre la imagen de la primera página.
La extracción usa `begin_analyze_document(...)` sobre el PDF completo.

La variable `AZURE_DOCUMENT_INTELLIGENCE_EXTRACTION_MODELS` debe ser un JSON con el mapeo entre etiqueta y `model_id`, por ejemplo:

```env
AZURE_DOCUMENT_INTELLIGENCE_EXTRACTION_MODELS={"Formato de cumplimiento":"modelo_fc","Entrada de mercancía":"modelo_em","Orden de compra A":"modelo_oca","Orden de compra B":"modelo_ocb"}
```

## Pruebas

```bash
pytest app/tests
```

## Limitaciones actuales

- La persistencia es en memoria; si reinicia la API, se pierde el historial.
- La clasificación usa la imagen de la primera página.
- La etiqueta devuelta depende exactamente de las clases configuradas en tu Custom Classification Model.
- La extracción depende de que exista un `model_id` configurado para la etiqueta detectada.
