import sys

with open("app/dashboard/streamlit_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Eliminar la declaracion de tabs original
old_tabs_decl = """    tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(
        [
            "📊 Resumen",
            "🚨 Alertas",
            "🧠 Causa Raíz",
            "🔬 Patrones",
            "🗂 Explorador",
            "🗄️ Historial",
        ]
    )"""

content = content.replace(old_tabs_decl, "")

# 2. Insertar la nueva declaracion de tabs antes de 'if "last_result" in st.session_state:'
new_tabs_decl = """
# Renderizar pestañas principales siempre visibles
tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(
    [
        "📊 Resumen",
        "🚨 Alertas",
        "🧠 Causa Raíz",
        "🔬 Patrones",
        "🗂 Explorador",
        "🗄️ Historial",
    ]
)

if "last_result" in st.session_state:"""

content = content.replace('if "last_result" in st.session_state:', new_tabs_decl, 1)

# 3. Separar `with tab_history:` y el bloque `else:`.
# El bloque `else:` está al final (renderiza el hero screen)
# Extraemos todo lo que hay desde `    with tab_history:` hasta `else:`
import re

history_pattern = re.compile(r'    with tab_history:\n.*?(?=\nelse:\n)', re.DOTALL)
match = history_pattern.search(content)

if match:
    history_block = match.group(0)
    # remover la indentacion adicional de 4 espacios
    new_history_block = "\n".join([line[4:] if line.startswith("    ") else line for line in history_block.split("\n")])
    
    # Remover el bloque original de dentro del if
    content = content[:match.start()] + "\n" + content[match.end():]
    
    # El final del archivo ahora es:
    # else:
    #     # Render welcome screen
    # ...
    
    # Vamos a insertar history_block antes de 'else:\n    # Render welcome screen'
    content = content.replace('else:\n    # Render welcome screen', new_history_block + '\n\nelse:\n    with tab_overview:\n        # Render welcome screen')
    
    # Y reemplazar las cosas en la bienvenida
    content = content.replace('        <div class="welcome-container">', '        st.markdown("""\n        <div class="welcome-container">', 1)
    
    # Agregar avisos a las otras tabs en el else
    welcome_end = '            st.session_state["welcome_run"] = True\n            st.rerun()'
    tabs_fallback = """            st.session_state["welcome_run"] = True
            st.rerun()

    with tab_alerts:
        st.info("Carga un archivo de logs en el panel lateral para ver las alertas.")
    with tab_root:
        st.info("El análisis de causa raíz aparecerá aquí.")
    with tab_patterns:
        st.info("Los patrones detectados aparecerán aquí.")
    with tab_data:
        st.info("El explorador de eventos estará disponible tras cargar datos.")
"""
    content = content.replace(welcome_end, tabs_fallback)
    
    with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Modificado exitosamente")
else:
    print("No se encontró el bloque tab_history")

