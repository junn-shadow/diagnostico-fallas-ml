ROOT_CAUSE_RULES = [
    (
        ("database", "db", "sql", "connection failed", "timeout", "query", "deadlock"),
        "Caída, saturación o interbloqueo en Base de Datos",
    ),
    (
        ("network", "connection", "unreachable", "refused", "tcp", "udp", "ospf", "bgp", "ftp", "http", "socket", "port", "interface", "link down"),
        "Falla de red, protocolo inestable o pérdida de conexión",
    ),
    (
        ("disk", "filesystem", "no space", "failure", "io error", "write", "read"),
        "Falla de disco, saturación de I/O o falta de espacio",
    ),
    (
        ("cpu", "memory", "oom", "usage high", "heap", "segfault", "killed"),
        "Saturación de CPU/RAM o proceso finalizado por OOM",
    ),
    (
        ("auth", "login", "permission", "denied", "unauthorized", "invalid token", "password"),
        "Fallo de autenticación o permisos insuficientes",
    ),
    (
        ("config", "syntax", "invalid value", "missing key", "parse error", "yaml"),
        "Error en configuración o formato inválido",
    ),
    (
        ("service", "daemon", "crashed", "exited", "stopped", "fatal"),
        "Caída crítica de servicio o demonio (Crash)",
    ),
]


def infer_root_cause(message: str) -> str:
    text = message.lower()
    for keywords, cause in ROOT_CAUSE_RULES:
        if any(keyword in text for keyword in keywords):
            return cause
    return "Comportamiento atípico no clasificado"
