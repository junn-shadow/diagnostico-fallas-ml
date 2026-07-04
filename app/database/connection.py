import os
import streamlit as st
import sqlalchemy as sa
from app.config.paths import DATABASE_PATH

def _get_secret_safe(key):
    val = None
    if key in os.environ:
        val = os.environ[key]
    else:
        try:
            val = st.secrets.get(key)
        except Exception:
            pass
    if val:
        return str(val).strip().strip("'").strip('"')
    return None

def get_connection():
    # 1. Intentamos buscar credenciales de Turso
    turso_url = _get_secret_safe("TURSO_DATABASE_URL")
    turso_token = _get_secret_safe("TURSO_AUTH_TOKEN")

    if turso_url and turso_token:
        db_url = turso_url
        if db_url.startswith("libsql://"):
            db_url = db_url.replace("libsql://", "sqlite+libsql://")
        elif not db_url.startswith("sqlite+libsql://"):
            db_url = f"sqlite+libsql://{db_url}"
            
        if "?" not in db_url:
            db_url = f"{db_url}?secure=true"
        elif "secure=" not in db_url:
            db_url = f"{db_url}&secure=true"
            
        engine = sa.create_engine(db_url, connect_args={"auth_token": turso_token})
        return engine.connect()

    # 2. Si no hay Turso, hacemos fallback a Supabase (PostgreSQL)
    supabase_url = _get_secret_safe("SUPABASE_URL")
        
    if supabase_url:
        engine = sa.create_engine(
            supabase_url,
            connect_args={"sslmode": "require"} if "supabase.com" in supabase_url or "pooler.supabase.com" in supabase_url else {}
        )
        return engine.connect()

    # 3. Fallback a SQLite local si no hay credenciales de nube
    db_path = os.getenv("SQLITE_DB_PATH", str(DATABASE_PATH))
    engine = sa.create_engine(f"sqlite:///{db_path}")
    return engine.connect()
