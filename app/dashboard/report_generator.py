import json
import pandas as pd
from datetime import datetime


def generate_html_report(logs: pd.DataFrame, result) -> str:
    """
    Genera un reporte HTML autocontenido con diseño premium de nivel ejecutivo.
    Utiliza fuentes de Google, gradients, tarjetas glassmorphic, y tablas responsivas.
    """
    alerts = logs[
        logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
    ].copy()
    if not alerts.empty:
        alerts = alerts.sort_values(
            ["is_anomaly", "anomaly_score"], ascending=[False, False]
        )

    # Formatear la fecha
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Contar severidades para el reporte
    levels_count = logs["level"].value_counts().to_dict()
    severity_distribution = ", ".join([f"{k}: {v}" for k, v in levels_count.items()])

    # Crear filas para la tabla de incidentes
    table_rows = ""
    if alerts.empty:
        table_rows = '<tr><td colspan="6" class="text-center">No se detectaron anomalías ni eventos críticos.</td></tr>'
    else:
        for idx, row in enumerate(alerts.head(150).itertuples()):
            lvl = getattr(row, "level", "UNKNOWN")
            badge_class = (
                f"badge-{lvl.lower()}"
                if lvl.lower()
                in ["info", "warning", "warn", "error", "critical", "fatal", "debug"]
                else "badge-other"
            )

            line = getattr(row, "line_id", "-")
            score = getattr(row, "anomaly_score", 0.0)
            tmpl = getattr(row, "event_template", "-")
            cause = getattr(row, "root_cause", "-")
            rec = getattr(row, "recommendation", "-")

            table_rows += f"""
            <tr>
                <td><strong>L{line}</strong></td>
                <td><span class="badge {badge_class}">{lvl}</span></td>
                <td>{score:.4f}</td>
                <td class="text-ellipsis" title="{tmpl}">{tmpl[:80]}...</td>
                <td><strong>{cause}</strong></td>
                <td>{rec}</td>
            </tr>
            """

    # Crear filas para el pipeline
    pipeline_rows = ""
    for stage in result.stages:
        status_class = f"status-{stage['status'].lower()}"
        pipeline_rows += f"""
        <div class="pipeline-card">
            <span class="pipeline-status {status_class}">{stage['status']}</span>
            <h4>{stage['stage']}</h4>
            <p>{stage['detail']}</p>
        </div>
        """

    # Executive Summary Text
    from app.dashboard.insights import build_executive_summary

    summary_data = build_executive_summary(logs)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Diagnóstico - DiagnosticOps ML</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-app: #f4f7fa;
            --bg-card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --accent-primary: #2563eb;
            --accent-gradient: linear-gradient(135deg, #2563eb 0%, #0f766e 100%);
            
            --color-info: #0ea5e9;
            --color-warning: #f59e0b;
            --color-error: #ef4444;
            --color-critical: #b91c1c;
            --color-stable: #10b981;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-app);
            color: var(--text-main);
            line-height: 1.6;
            padding: 2.5rem 1.5rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        /* Header Style */
        header {{
            background: var(--accent-gradient);
            padding: 2.5rem;
            border-radius: 16px;
            color: white;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.15);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }}

        header::after {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 350px;
            height: 350px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.05);
            pointer-events: none;
        }}

        .header-eyebrow {{
            text-transform: uppercase;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            color: rgba(255, 255, 255, 0.85);
            margin-bottom: 0.5rem;
            display: inline-block;
        }}

        header h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }}

        .header-meta {{
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.8);
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            margin-top: 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.15);
            padding-top: 1rem;
        }}

        .header-meta span strong {{
            color: white;
        }}

        /* Grid Layout */
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .col-2 {{
            grid-column: span 2;
        }}

        .col-3 {{
            grid-column: span 3;
        }}

        /* Card Styles */
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }}

        .card-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}

        .metric-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }}

        .metric-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--accent-primary);
        }}

        .metric-sub {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.15rem;
        }}

        /* Executive Insights */
        .executive-box {{
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1.25rem;
        }}

        .executive-box p {{
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
            color: #334155;
        }}

        .executive-box p:last-child {{
            margin-bottom: 0;
        }}

        /* Pipeline Steps */
        .pipeline-container {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .pipeline-card {{
            background: #fafafa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .pipeline-card h4 {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-main);
            flex: 1;
        }}

        .pipeline-card p {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-right: 1.5rem;
        }}

        .pipeline-status {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            text-transform: uppercase;
        }}

        .status-completado {{
            background: #dcfce7;
            color: #166534;
        }}

        .status-degradado {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .status-omitido {{
            background: #e2e8f0;
            color: #475569;
        }}

        /* Table design */
        .table-wrapper {{
            overflow-x: auto;
            margin-top: 0.5rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }}

        th {{
            background-color: #f8fafc;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.7rem;
            letter-spacing: 0.05em;
            padding: 0.85rem 1rem;
            border-bottom: 2px solid var(--border-color);
        }}

        td {{
            padding: 0.85rem 1rem;
            border-bottom: 1px solid var(--border-color);
            color: #334155;
            vertical-align: middle;
        }}

        tr:hover td {{
            background-color: #f8fafc;
        }}

        .text-center {{
            text-align: center;
        }}

        .text-ellipsis {{
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }}

        .badge-info {{ background-color: #e0f2fe; color: #0369a1; }}
        .badge-warning, .badge-warn {{ background-color: #fef3c7; color: #b45309; }}
        .badge-error {{ background-color: #fee2e2; color: #b91c1c; }}
        .badge-critical, .badge-fatal {{ background-color: #fecdd3; color: #9f1239; }}
        .badge-debug {{ background-color: #f1f5f9; color: #475569; }}
        .badge-other {{ background-color: #f3e8ff; color: #6b21a8; }}

        footer {{
            margin-top: 3rem;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border-color);
            padding-top: 1.5rem;
        }}

        @media (max-width: 850px) {{
            .grid, .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            .col-2, .col-3 {{
                grid-column: span 1;
            }}
            body {{
                padding: 1rem;
            }}
            header {{
                padding: 1.5rem;
            }}
            header h1 {{
                font-size: 1.7rem;
            }}
        }}

        /* @media print styles to enable seamless Save-to-PDF formatting */
        @media print {{
            body {{
                background: white !important;
                color: black !important;
                padding: 0 !important;
                font-size: 10pt !important;
            }}
            .container {{
                max-width: 100% !important;
                margin: 0 !important;
            }}
            header {{
                background: none !important;
                background-color: #f8fafc !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                box-shadow: none !important;
                padding: 1.5rem !important;
                page-break-inside: avoid;
            }}
            header h1 {{
                color: #0f172a !important;
                font-size: 1.8rem !important;
            }}
            header::after {{
                display: none !important;
            }}
            .header-meta {{
                border-top: 1px solid #94a3b8 !important;
                color: #334155 !important;
                padding-top: 0.5rem !important;
            }}
            .header-meta span strong {{
                color: black !important;
            }}
            .metric-card, .card, .executive-box, .pipeline-card {{
                box-shadow: none !important;
                border: 1px solid #cbd5e1 !important;
                background: white !important;
                page-break-inside: avoid !important;
            }}
            .metric-value {{
                color: #0284c7 !important;
            }}
            table {{
                page-break-inside: auto;
            }}
            tr {{
                page-break-inside: avoid !important;
                page-break-after: auto;
            }}
            thead {{
                display: table-header-group;
            }}
            footer {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="header-eyebrow">DiagnosticOps ML — Reporte de Diagnóstico</span>
            <h1>Análisis Automatizado de Incidencias</h1>
            <p>Detección de anomalías no supervisada y estructuración semántica de logs.</p>
            
            <div class="header-meta">
                <span>Archivo Fuente: <strong>{result.log_source}</strong></span>
                <span>ID de Ejecución: <strong>{result.run_id}</strong></span>
                <span>Generado el: <strong>{date_str}</strong></span>
            </div>
        </header>

        <!-- Métricas Principales -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Logs Analizados</div>
                <div class="metric-value">{len(logs):,}</div>
                <div class="metric-sub">Eventos procesados en pipeline</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Anomalías Detectadas</div>
                <div class="metric-value" style="color: var(--color-error);">{result.anomaly_count}</div>
                <div class="metric-sub">Tasa de anomalía: {((result.anomaly_count/len(logs)*100) if len(logs) else 0):.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Eventos de Error / Críticos</div>
                <div class="metric-value" style="color: var(--color-critical);">{int(logs["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())}</div>
                <div class="metric-sub">Distribución: {severity_distribution}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Coeficiente Silueta (ML)</div>
                <div class="metric-value" style="color: var(--color-stable);">{result.silhouette_score:.4f}</div>
                <div class="metric-sub">Davies-Bouldin: {result.davies_bouldin_index:.4f}</div>
            </div>
        </div>

        <!-- Secciones de Resumen y Pipeline -->
        <div class="grid">
            <div class="card col-2">
                <div class="card-title">Resumen Ejecutivo de Operación</div>
                <div class="executive-box">
                    <p><strong>Dominio de Servicio Probable:</strong> {summary_data["domain"]}</p>
                    <p><strong>Postura Operativa:</strong> {summary_data["posture"]}</p>
                    <p><strong>Volumen del Incidente:</strong> {summary_data["volume"]}</p>
                    <p><strong>Acción Recomendada:</strong> {summary_data["focus"]}</p>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Pipeline de Análisis</div>
                <div class="pipeline-container">
                    {pipeline_rows}
                </div>
            </div>
        </div>

        <!-- Tabla de Alertas Priorizadas -->
        <div class="card col-3">
            <div class="card-title">
                <span>Bandeja de Eventos Críticos y Anomalías ML (Top 150)</span>
                <span style="font-size: 0.8rem; font-weight: normal; color: var(--text-muted);">Clasificado por riesgo y probabilidad</span>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 8%;">Línea</th>
                            <th style="width: 10%;">Severidad</th>
                            <th style="width: 10%;">Score ML</th>
                            <th style="width: 32%;">Plantilla Drain</th>
                            <th style="width: 20%;">Causa Raíz Probable</th>
                            <th style="width: 20%;">Acción Sugerida</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>DiagnosticOps ML &copy; {datetime.now().year} — Reporte de Análisis y Diagnóstico de Fallas.</p>
        </footer>
    </div>
</body>
</html>
"""
    return html_content


def generate_json_report(logs: pd.DataFrame, result) -> str:
    """
    Genera un payload JSON estructurado con toda la metadata del análisis.
    """
    alerts = logs[
        logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
    ].copy()
    if not alerts.empty:
        alerts = alerts.sort_values(
            ["is_anomaly", "anomaly_score"], ascending=[False, False]
        )

    # Formatear la lista de alertas
    alert_list = []
    for row in alerts.head(500).itertuples():
        alert_list.append(
            {
                "line_id": int(getattr(row, "line_id")),
                "level": str(getattr(row, "level")),
                "is_anomaly": bool(getattr(row, "is_anomaly")),
                "anomaly_score": float(getattr(row, "anomaly_score", 0.0)),
                "event_template": str(getattr(row, "event_template", "")),
                "root_cause": str(getattr(row, "root_cause", "")),
                "recommendation": str(getattr(row, "recommendation", "")),
            }
        )

    from app.dashboard.insights import build_executive_summary

    summary_data = build_executive_summary(logs)

    report_data = {
        "metadata": {
            "run_id": result.run_id,
            "log_source": result.log_source,
            "timestamp": datetime.now().isoformat(),
            "analyzer_version": "1.0.0",
        },
        "stats": {
            "total_lines": len(logs),
            "anomaly_count": result.anomaly_count,
            "anomaly_rate": (result.anomaly_count / len(logs)) if len(logs) else 0.0,
            "error_count": int(
                logs["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum()
            ),
            "severity_counts": logs["level"].value_counts().to_dict(),
            "silhouette_score": float(result.silhouette_score),
            "davies_bouldin_index": float(result.davies_bouldin_index),
        },
        "executive_summary": summary_data,
        "pipeline_stages": result.stages,
        "top_alerts": alert_list,
    }

    return json.dumps(report_data, indent=2, ensure_ascii=False)


def generate_csv_report(logs: pd.DataFrame) -> str:
    """
    Retorna el dataframe de alertas filtrado en formato CSV listo para descargar.
    """
    alerts = logs[
        logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
    ].copy()
    if not alerts.empty:
        alerts = alerts.sort_values(
            ["is_anomaly", "anomaly_score"], ascending=[False, False]
        )

    columns_to_export = [
        "line_id",
        "level",
        "is_anomaly",
        "anomaly_score",
        "event_template",
        "root_cause",
        "recommendation",
        "clean_log",
    ]

    # Asegurar que solo exportamos columnas existentes
    cols = [c for c in columns_to_export if c in alerts.columns]

    return alerts[cols].to_csv(index=False)
