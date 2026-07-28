from __future__ import annotations

import json
import os
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "http://localhost:8000")
CLARO_LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/0/0c/Claro.svg"


def inject_styles() -> None:
    """Inject custom CSS for a more polished branded UI."""
    st.markdown(
        """
        <style>
        :root {
            --claro-red: #d71920;
            --claro-red-dark: #a80f15;
            --claro-soft: #fff2f3;
            --surface: #ffffff;
            --border: #f1c7ca;
            --text: #221517;
            --muted: #74595c;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(215, 25, 32, 0.12), transparent 30%),
                linear-gradient(180deg, #fff9f9 0%, #fff4f5 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.1rem;
            padding-bottom: 2.5rem;
        }

        .hero-shell {
            position: relative;
            background:
                radial-gradient(circle at 12% 50%, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.03) 18%, transparent 38%),
                linear-gradient(135deg, #d71920 0%, #bf141b 52%, #a80f15 100%);
            border: none;
            border-radius: 28px;
            padding: 1rem 1.25rem;
            box-shadow:
                0 20px 44px rgba(116, 34, 40, 0.16),
                inset 0 1px 0 rgba(255, 255, 255, 0.12);
            margin: 0.35rem 0 1rem 0;
            overflow: hidden;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -8% -65% 28%;
            height: 150px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0.08) 26%, transparent 62%);
            filter: blur(18px);
            pointer-events: none;
        }

        .hero-logo-wrap {
            position: relative;
            z-index: 1;
            background: transparent;
            border: none;
            border-radius: 18px;
            padding: 0.9rem 1.15rem;
            min-height: 112px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            box-shadow: none;
            backdrop-filter: none;
        }

        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 1rem 1.1rem 0.95rem 1.1rem;
            box-shadow: 0 14px 35px rgba(116, 34, 40, 0.06);
            margin-bottom: 0.55rem;
        }

        .kpi-card {
            background: linear-gradient(180deg, #ffffff 0%, #fff7f7 100%);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1rem;
            min-height: 118px;
            box-shadow: 0 10px 24px rgba(116, 34, 40, 0.06);
        }

        .kpi-label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .kpi-value {
            color: var(--claro-red-dark);
            font-size: 1.35rem;
            line-height: 1.15;
            font-weight: 800;
            word-break: break-word;
        }

        .section-title {
            color: var(--text);
            font-size: 1.04rem;
            font-weight: 800;
            margin-bottom: 0;
        }

        .section-copy {
            color: var(--muted);
            font-size: 0.94rem;
            margin-bottom: 0.75rem;
        }

        .panel-gap {
            height: 0.25rem;
        }

        .json-panel {
            background: #fffafa;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1rem;
            color: var(--text);
            font-size: 0.92rem;
            line-height: 1.45;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 24px rgba(116, 34, 40, 0.05);
        }

        .data-table thead th {
            background: linear-gradient(135deg, var(--claro-red) 0%, #ef3c43 100%);
            color: white;
            text-align: left;
            padding: 0.72rem 0.8rem;
            font-size: 0.88rem;
        }

        .data-table tbody td {
            padding: 0.55rem 0.72rem;
            border-top: 1px solid #f5d7d9;
            color: var(--text);
            vertical-align: top;
            font-size: 0.9rem;
            line-height: 1.25;
        }

        .data-table tbody tr:nth-child(odd) {
            background: #fff8f8;
        }

        .field-name {
            font-weight: 700;
            color: var(--claro-red-dark);
            min-width: 170px;
            width: 34%;
        }

        .stButton > button, .stDownloadButton > button {
            background: linear-gradient(135deg, var(--claro-red) 0%, #ef3c43 100%);
            color: white;
            border: none;
            border-radius: 999px;
            font-weight: 800;
            padding: 0.65rem 1.2rem;
            box-shadow: 0 12px 28px rgba(215, 25, 32, 0.25);
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            background: linear-gradient(135deg, var(--claro-red-dark) 0%, var(--claro-red) 100%);
            color: white;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(180deg, #ffffff 0%, #fff4f5 100%);
            border: 2px dashed #e59aa0;
            border-radius: 22px;
            padding: 1rem;
            box-shadow: none;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--claro-red);
            background: linear-gradient(180deg, #fff9f9 0%, #ffeef0 100%);
        }

        [data-testid="stFileUploaderDropzone"] * {
            color: var(--text) !important;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: var(--muted) !important;
        }

        [data-testid="stFileUploader"] > label,
        [data-testid="stFileUploader"] > label p,
        [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p {
            color: var(--claro-red-dark) !important;
            font-weight: 800 !important;
        }

        [data-testid="stBaseButton-secondary"] {
            background: white !important;
            color: var(--claro-red-dark) !important;
            border: 1px solid #e59aa0 !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
        }

        [data-testid="stBaseButton-secondary"]:hover {
            border-color: var(--claro-red) !important;
            color: var(--claro-red) !important;
        }

        .footer-note {
            color: var(--muted);
            font-size: 0.88rem;
            text-align: center;
            margin-top: 1rem;
        }

        header[data-testid="stHeader"] {
            background: transparent;
            border-bottom: none;
            backdrop-filter: none;
        }

        [data-testid="stHeader"] * {
            color: var(--text) !important;
        }

        [data-testid="stHeader"] button,
        [data-testid="stHeader"] a {
            color: var(--text) !important;
        }

        .process-card {
            background: #fffafa;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin: 0.4rem 0 1rem 0;
        }

        .process-title {
            color: var(--claro-red-dark);
            font-weight: 800;
            font-size: 0.98rem;
            margin-bottom: 0.55rem;
        }

        .process-line {
            color: var(--text);
            font-size: 0.92rem;
            line-height: 1.35;
            margin: 0.2rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render a clean top header with only the brand logo."""
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-logo-wrap">
                <img src="{CLARO_LOGO_URL}" style="max-width:260px; max-height:82px; width:auto; height:auto; display:block; margin:0;" />
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str) -> None:
    """Render a styled KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_json_panel(payload: dict[str, Any]) -> None:
    """Render JSON output with light styling."""
    json_text = json.dumps(payload, indent=2, ensure_ascii=False)
    escaped = (
        json_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    st.markdown(
        f'<div class="json-panel"><pre style="margin:0; white-space:pre-wrap;">{escaped}</pre></div>',
        unsafe_allow_html=True,
    )


def render_table(rows: list[dict[str, Any]]) -> None:
    """Render a light HTML table instead of Streamlit's dark dataframe."""
    body = "".join(
        f"<tr><td class='field-name'>{row['field']}</td><td>{row['value']}</td></tr>"
        for row in rows
    )
    table_html = f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Campo</th>
                <th>Valor</th>
            </tr>
        </thead>
        <tbody>
            {body}
        </tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def render_layout_tables(tables: list[dict[str, Any]]) -> None:
    """Render layout tables extracted by Azure prebuilt-layout."""
    if not tables:
        st.info("No se detectaron tablas de layout en este documento.")
        return

    for table in tables:
        page_numbers = ", ".join(str(page) for page in table.get("page_numbers", [])) or "N/A"
        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-title">Tabla {table.get("table_index", "")}</div>
                <div class="section-copy">
                    Páginas: {page_numbers} | Filas: {table.get("row_count", 0)} | Columnas: {table.get("column_count", 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        header_fields = table.get("header_fields", [])
        if header_fields:
            header_rows = "".join(
                f"<tr><td class='field-name'>{header.get('merged_label') or header.get('content')}</td><td>{header.get('content')}</td></tr>"
                for header in header_fields
            )
            st.markdown(
                f"""
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Encabezado unificado</th>
                            <th>Valor encabezado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {header_rows}
                    </tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)

        rows = table.get("rows", [])
        if not rows:
            continue

        header_cells = "".join(
            f"<th>Columna {index + 1}</th>" for index in range(len(rows[0]))
        )
        body_rows = "".join(
            "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        st.markdown(
            f"""
            <table class="data-table">
                <thead>
                    <tr>{header_cells}</tr>
                </thead>
                <tbody>
                    {body_rows}
                </tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)


def render_process_summary() -> None:
    """Render a visible processing summary."""
    st.markdown(
        """
        <div class="process-card">
            <div class="process-title">Proceso finalizado</div>
            <div class="process-line">Enviando archivo al backend</div>
            <div class="process-line">Clasificación completada</div>
            <div class="process-line">Extracción completada</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Document AI Pipeline", layout="wide", menu_items={})
    inject_styles()
    render_header()

    if "processed_result" not in st.session_state:
        st.session_state.processed_result = None

    uploaded_file = st.file_uploader("Selecciona un PDF", type=["pdf"])

    if uploaded_file and st.button("Procesar documento", type="primary"):
        with st.spinner("Procesando PDF..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                response = requests.post(
                    f"{API_BASE_URL}/upload",
                    files=files,
                    timeout=120,
                )
            except requests.RequestException as exc:
                st.error(f"No se pudo conectar con el backend: {exc}")
                return

            if response.status_code != 200:
                detail = response.json().get("detail", "Error desconocido.")
                st.error(detail)
                return

            st.session_state.processed_result = response.json()

    result = st.session_state.processed_result

    if result:
        render_process_summary()

        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Resultado del procesamiento</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Formato detectado", result["document_type"])
        with col2:
            render_kpi_card("Confianza", f'{(result.get("confidence") or 0):.2%}')
        with col3:
            render_kpi_card("Tiempo", f'{result["processing_time_ms"]} ms')

        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.markdown(
                """
                <div class="section-card">
                    <div class="section-title">Resumen técnico</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)
            render_json_panel(
                {
                    "id": result["id"],
                    "document_type": result["document_type"],
                    "confidence": result.get("confidence"),
                    "layout_tables_count": len(result.get("layout_tables", [])),
                    "layout_header_count": len(result.get("layout_headers", {}).get("all_headers", [])),
                    "processing_time_ms": result["processing_time_ms"],
                    "created_at": result["created_at"],
                }
            )

        with right_col:
            st.markdown(
                """
                <div class="section-card">
                    <div class="section-title">JSON extraído</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)
            render_json_panel(result["data"])

        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Campos extraídos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)
        render_table(flatten_payload(result["data"]))

        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Encabezados unificados de tablas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)
        render_json_panel(result.get("layout_headers", {}))

        st.markdown(
            """
            <div class="section-card">
                <div class="section-title">Tablas de layout</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="panel-gap"></div>', unsafe_allow_html=True)
        render_layout_tables(result.get("layout_tables", []))

        st.download_button(
            label="Descargar resultado JSON",
            data=json.dumps(result["data"], indent=2, ensure_ascii=False),
            file_name=f'datos_extraidos_{result["id"]}.json',
            mime="application/json",
        )

    st.markdown(
        '<div class="footer-note">Claro | Automatización documental con Azure AI Document Intelligence</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
