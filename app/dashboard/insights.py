import pandas as pd

DOMAIN_KEYWORDS = {
    "Base de datos": (
        "database",
        "db",
        "sql",
        "mysql",
        "postgres",
        "oracle",
        "connection failed",
    ),
    "Red / conectividad": (
        "network",
        "timeout",
        "unreachable",
        "refused",
        "socket",
        "connection",
    ),
    "Disco / almacenamiento": ("disk", "filesystem", "volume", "space", "io error"),
    "Recursos del servidor": ("cpu", "memory", "oom", "heap", "usage high", "thread"),
    "Autenticacion": ("auth", "login", "permission", "denied", "token", "credential"),
    "Aplicacion web": ("http", "request", "response", "endpoint", "server", "service"),
}


def infer_log_domain(logs: pd.DataFrame) -> list[tuple[str, int]]:
    text = " ".join(
        logs["clean_log"].fillna(logs["raw_log"]).astype(str).str.lower().head(20000)
    )
    scores = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(text.count(keyword) for keyword in keywords)
        if score:
            scores.append((domain, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def build_executive_summary(logs: pd.DataFrame) -> dict[str, str]:
    total = len(logs)
    anomalies = int(logs["is_anomaly"].sum()) if "is_anomaly" in logs else 0
    critical = (
        int(logs["level"].isin(["CRITICAL", "FATAL"]).sum()) if "level" in logs else 0
    )
    errors = (
        int(logs["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())
        if "level" in logs
        else 0
    )
    domains = infer_log_domain(logs)
    main_domain = domains[0][0] if domains else "Operacion general del servidor"

    if critical:
        posture = "El archivo contiene eventos criticos que deben revisarse con prioridad alta."
    elif anomalies or errors:
        posture = "El archivo muestra senales de degradacion o comportamiento inusual."
    else:
        posture = "El archivo no muestra senales fuertes de incidente con los filtros actuales."

    if anomalies:
        focus = "Prioriza las filas marcadas por ML y cruza su plantilla Drain con la causa raiz sugerida."
    elif errors:
        focus = "Prioriza eventos ERROR/CRITICAL y revisa su repeticion por plantilla."
    else:
        focus = "Usa el explorador para validar patrones repetidos y establecer una linea base."

    return {
        "domain": main_domain,
        "posture": posture,
        "focus": focus,
        "volume": f"{total:,} eventos procesados, {errors:,} errores y {anomalies:,} anomalias.",
    }


def top_templates(logs: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    if "event_template" not in logs:
        return pd.DataFrame(columns=["event_template", "cantidad"])
    return (
        logs.groupby("event_template")
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
        .head(limit)
    )
