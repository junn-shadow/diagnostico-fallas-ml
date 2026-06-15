import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config.settings import SEVERITY_WEIGHTS


def build_features(logs: pd.DataFrame):
    """Return numeric features plus fitted vectorizer metadata."""
    df = logs.copy()
    text = df["event_template"].fillna("")
    vectorizer = TfidfVectorizer(max_features=256, ngram_range=(1, 2))
    tfidf = vectorizer.fit_transform(text)

    numeric = pd.DataFrame(
        {
            "severity": df["level"].map(SEVERITY_WEIGHTS).fillna(1).astype(float),
            "template_frequency": df.groupby("event_template")["event_template"].transform("count").astype(float),
            "message_length": df["clean_log"].fillna(df["raw_log"]).astype(str).str.len().astype(float),
        }
    )
    return tfidf, numeric, vectorizer
