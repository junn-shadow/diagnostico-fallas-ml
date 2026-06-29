import re
import pandas as pd
import unicodedata

SPACE_RE = re.compile(r"\s+")


def clean_message(message) -> str:
    if pd.isna(message):
        return ""
    msg_str = str(message)
    # Normalizar unicode (elimina variaciones visuales y caracteres ocultos)
    msg_str = unicodedata.normalize("NFKC", msg_str)
    msg_str = msg_str.replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()
    return SPACE_RE.sub(" ", msg_str)


def clean_logs(logs: pd.DataFrame) -> pd.DataFrame:
    df = logs.copy()
    df["clean_log"] = df["raw_log"].map(clean_message)
    return df
