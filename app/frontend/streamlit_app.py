from __future__ import annotations

import json
import os
from typing import Any
import requests
import streamlit as st


API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "http://localhost:8000")


def flatten_payload(payload: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    """Flatten nested JSON for table display."""
    rows: list[dict[str, Any]] = []
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            rows.extend(flatten_payload(value, full_key))
        elif isinstance(value, list):
            rows.append({"field": full_key, "value": json.dumps(value, ensure_ascii=False)})
        else:
            rows.append({"field": full_key, "value": value})
    return rows


def main() -> None:
    st.set_page_config(page_title="Document AI Pipeline", layout="wide")
    st.title("Document AI Pipeline")
    st.write(
        "Sube un PDF. Se clasifica usando la primera página y luego se enruta al "
        "modelo de extracción configurado para ese tipo documental."
    )

    uploaded_file = st.file_uploader("Selecciona un PDF", type=["pdf"])

    if uploaded_file and st.button("Procesar documento", type="primary"):
        with st.status("Procesando PDF...", expanded=True) as status:
            status.write("1. Enviando archivo al backend")
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                response = requests.post(
                    f"{API_BASE_URL}/upload",
                    files=files,
                    timeout=120,
                )
            except requests.RequestException as exc:
                status.update(label="Error de conexión", state="error")
                st.error(f"No se pudo conectar con el backend: {exc}")
                return

            if response.status_code != 200:
                status.update(label="Error de procesamiento", state="error")
                detail = response.json().get("detail", "Error desconocido.")
                st.error(detail)
                return

            status.write("2. Clasificación completada")
            status.write("3. Extracción completada")
            status.update(label="Proceso finalizado", state="complete")
            result = response.json()

        col1, col2, col3 = st.columns(3)
        col1.metric("Tipo detectado", result["document_type"])
        col2.metric("Confianza", f'{(result.get("confidence") or 0):.2%}')
        col3.metric("Tiempo", f'{result["processing_time_ms"]} ms')

        st.subheader("Resultado de clasificación")
        st.json(
            {
                "id": result["id"],
                "document_type": result["document_type"],
                "confidence": result.get("confidence"),
                "processing_time_ms": result["processing_time_ms"],
                "created_at": result["created_at"],
            }
        )

        st.subheader("Datos extraídos")
        st.json(result["data"])

        st.subheader("Tabla de campos")
        st.dataframe(flatten_payload(result["data"]), use_container_width=True)

        st.download_button(
            label="Descargar resultado JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name=f'documento_{result["id"]}.json',
            mime="application/json",
        )


if __name__ == "__main__":
    main()
