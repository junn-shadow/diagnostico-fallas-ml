import re


LOG_PATTERN = re.compile(
    r"(?P<timestamp>\S+)\s+"
    r"(?P<level>INFO|ERROR|WARNING|CRITICAL|DEBUG)\s+"
    r"(?P<message>.*)"
)


def parse_logs(logs):
    """
    Convierte logs en estructura JSON/dict.
    """

    parsed = []

    for log in logs:

        match = LOG_PATTERN.match(log)

        if match:
            parsed.append({
                "timestamp": match.group("timestamp"),
                "level": match.group("level"),
                "message": match.group("message")
            })

    return parsed