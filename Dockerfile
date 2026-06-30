# Usa la versión slim de Python
FROM python:3.11-slim

# Crea un usuario no root (obligatorio para evitar errores de permisos en HF)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copia los requirements con los permisos correctos
COPY --chown=user requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código
COPY --chown=user . .

# Expone el puerto 7860
EXPOSE 7860

# Ejecuta Streamlit apuntando a tu archivo específico
CMD ["streamlit", "run", "app/dashboard/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=7860"]