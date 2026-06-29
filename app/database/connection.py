import os
import streamlit as st
import sqlalchemy as sa

def get_connection():
    # 1. Buscamos primero en los Secrets de Streamlit (tanto local como en la nube)
    if "SUPABASE_URL" in st.secrets:
        db_url = st.secrets["SUPABASE_URL"]
    else:
        # Alternativa por si se ejecuta fuera de Streamlit (ej. un script de terminal)
        db_url = os.getenv("SUPABASE_URL")
        
    if not db_url:
        raise RuntimeError(
            "⚠️ No se encontró la variable SUPABASE_URL. "
            "Asegúrate de agregarla en .streamlit/secrets.toml localmente o en los Secrets de Streamlit Cloud."
        )

    # 2. Creamos la conexión con SQLAlchemy
    # Supabase (PostgreSQL) requiere SSL para conectarse de forma segura.
    engine = sa.create_engine(
        db_url,
        connect_args={"sslmode": "require"} if "supabase.com" in db_url or "pooler.supabase.com" in db_url else {}
    )
    return engine.connect()

