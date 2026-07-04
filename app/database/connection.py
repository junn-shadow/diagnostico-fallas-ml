import os
import streamlit as st
import sqlalchemy as sa

def get_connection():
    # 1. Intentamos buscar credenciales de Turso (Bajo libSQL/SQLite en la nube)
    turso_url = st.secrets.get("TURSO_DATABASE_URL") or os.getenv("TURSO_DATABASE_URL")
    turso_token = st.secrets.get("TURSO_AUTH_TOKEN") or os.getenv("TURSO_AUTH_TOKEN")

    if turso_url and turso_token:
        # Si la URL viene como libsql://, la adaptamos para SQLAlchemy con sqlite+libsql://
        db_url = turso_url
        if db_url.startswith("libsql://"):
            db_url = db_url.replace("libsql://", "sqlite+libsql://")
        elif not db_url.startswith("sqlite+libsql://"):
            db_url = f"sqlite+libsql://{db_url}"
            
        # Para evitar el error 308 Permanent Redirect, nos aseguramos de usar conexión segura
        if "?" not in db_url:
            db_url = f"{db_url}?secure=true"
        elif "secure=" not in db_url:
            db_url = f"{db_url}&secure=true"
            
        # Conexión a Turso utilizando el dialecto de libsql
        engine = sa.create_engine(
            db_url,
            connect_args={"auth_token": turso_token}
        )
        return engine.connect()

    # 2. Si no hay Turso, hacemos fallback a Supabase (PostgreSQL)
    supabase_url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        
    if not supabase_url:
        raise RuntimeError(
            "⚠️ No se encontró la variable de conexión de base de datos (TURSO_DATABASE_URL o SUPABASE_URL). "
            "Asegúrate de agregar alguna en .streamlit/secrets.toml localmente o en los Secrets de tu hosting."
        )

    # Conexión a Supabase (PostgreSQL) que requiere SSL para conectarse de forma segura.
    engine = sa.create_engine(
        supabase_url,
        connect_args={"sslmode": "require"} if "supabase.com" in supabase_url or "pooler.supabase.com" in supabase_url else {}
    )
    return engine.connect()

