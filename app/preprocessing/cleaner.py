import re
import pandas as pd


SPACE_RE = re.compile(r"\s+")


def clean_message(message: str) -> str:
    message = message.replace("\t", " ").strip()
    return SPACE_RE.sub(" ", message)


def clean_logs(logs: pd.DataFrame) -> pd.DataFrame:
    df = logs.copy()
    df["clean_log"] = df["raw_log"].astype(str).map(clean_message)
    return df
