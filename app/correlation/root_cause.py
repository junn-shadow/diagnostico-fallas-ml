ROOT_CAUSE_RULES = [
    (("database", "db", "sql", "connection failed", "timeout"), "Posible caida o saturacion de base de datos"),
    (("network", "connection", "unreachable", "refused"), "Posible problema de red o servicio no disponible"),
    (("disk", "filesystem", "no space", "failure"), "Posible falla de disco o falta de espacio"),
    (("cpu", "memory", "oom", "usage high"), "Posible saturacion de recursos del servidor"),
    (("auth", "login", "permission", "denied"), "Posible problema de autenticacion o permisos"),
]


def infer_root_cause(message: str) -> str:
    text = message.lower()
    for keywords, cause in ROOT_CAUSE_RULES:
        if any(keyword in text for keyword in keywords):
            return cause
    return "Anomalia detectada; requiere revision tecnica"
