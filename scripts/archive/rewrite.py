import re

with open("app/dashboard/streamlit_app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_history_tab = False
history_tab_lines = []
in_else_block = False
else_lines = []

# Identificar secciones
i = 0
while i < len(lines):
    line = lines[i]
    
    # Eliminar la definicion original de tabs
    if line.strip() == 'tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(':
        # saltar las siguientes lineas hasta '    )'
        while i < len(lines) and lines[i].strip() != ')':
            i += 1
        i += 1
        continue
        
    # Encontrar el inicio de "with tab_history:"
    if line.startswith('    with tab_history:'):
        in_history_tab = True
        history_tab_lines.append(line)
        i += 1
        # Recolectar todo el tab_history hasta el else: del if "last_result" in st.session_state
        while i < len(lines) and not lines[i].startswith('else:'):
            history_tab_lines.append(lines[i])
            i += 1
        in_history_tab = False
        continue
        
    # Encontrar el "else:" (pantalla de bienvenida)
    if line.startswith('else:') and 'last_result' not in line: # Es el else del final
        in_else_block = True
        else_lines.append(line)
        i += 1
        while i < len(lines):
            else_lines.append(lines[i])
            i += 1
        break

    new_lines.append(line)
    i += 1

# Ahora reconstruir
final_code = []
for line in new_lines:
    if line.startswith('if "last_result" in st.session_state:'):
        final_code.append('\n# Renderizar pestañas principales siempre visibles\n')
        final_code.append('tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs([\n')
        final_code.append('    "📊 Resumen", "🚨 Alertas", "🧠 Causa Raíz", "🔬 Patrones", "🗂 Explorador", "🗄️ Historial"\n')
        final_code.append('])\n\n')
        
        # Insertar el tab_history AQUI, fuera del if last_result
        for h_line in history_tab_lines:
            # quitarle 4 espacios de indentacion ya que estara fuera del if
            if h_line.startswith('    '):
                final_code.append(h_line[4:])
            else:
                final_code.append(h_line)
        
        final_code.append('\n')
        final_code.append(line)
    else:
        final_code.append(line)

# Añadir el bloque else modificado
final_code.append('else:\n')
final_code.append('    with tab_overview:\n')
for e_line in else_lines[1:]: # omit the "else:\n"
    final_code.append('    ' + e_line)
final_code.append('    with tab_alerts:\n        st.info("Carga un archivo de logs en el panel lateral o usa el dataset de muestra para ver las alertas.")\n')
final_code.append('    with tab_root:\n        st.info("El análisis de causa raíz aparecerá aquí.")\n')
final_code.append('    with tab_patterns:\n        st.info("Los patrones detectados aparecerán aquí.")\n')
final_code.append('    with tab_data:\n        st.info("El explorador de eventos estará disponible tras cargar datos.")\n')


with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
    f.writelines(final_code)

print("Modificacion completada")
