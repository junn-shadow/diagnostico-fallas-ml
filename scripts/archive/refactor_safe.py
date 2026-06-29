with open("app/dashboard/streamlit_app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of the `if "last_result"` block
if_idx = -1
for i, line in enumerate(lines):
    if line.startswith('if "last_result" in st.session_state:'):
        if_idx = i
        break

# Find the `else:` block at the end
else_idx = -1
for i in range(len(lines)-1, -1, -1):
    if lines[i].startswith('else:'):
        else_idx = i
        break

# Find `    with tab_history:`
history_idx = -1
for i in range(if_idx, else_idx):
    if lines[i].startswith('    with tab_history:'):
        history_idx = i
        break

# Extract the history block
history_lines = lines[history_idx:else_idx]
# Unindent history lines by 4 spaces
new_history_lines = []
for line in history_lines:
    if line.startswith('    '):
        new_history_lines.append(line[4:])
    else:
        new_history_lines.append(line)

# The content before the `if` block
part1 = lines[:if_idx]

# The tabs declaration to insert
tabs_decl = [
    '# Renderizar pestañas principales siempre visibles\n',
    'tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs([\n',
    '    "📊 Resumen", "🚨 Alertas", "🧠 Causa Raíz", "🔬 Patrones", "🗂 Explorador", "🗄️ Historial"\n',
    '])\n\n'
]

part1.extend(tabs_decl)
part1.append(lines[if_idx]) # The if line

# The content inside the if block, BEFORE the history block
part2 = lines[if_idx+1:history_idx]

# We need to remove the original tabs declaration from part2
cleaned_part2 = []
skip = False
for line in part2:
    if 'tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(' in line:
        skip = True
        continue
    if skip and ')' in line:
        skip = False
        continue
    if not skip:
        cleaned_part2.append(line)

part2 = cleaned_part2

# The history block goes AFTER the if block (which ends at else_idx)
# So we close the if block implicitly because we removed history from it, and else is right after.
# Wait, the else block was for `if "last_result" in st.session_state:`.
# We need to modify the else block so it uses `with tab_overview:` for the welcome screen, 
# and add fallbacks for the other tabs.

else_lines = lines[else_idx:]
new_else_lines = ['else:\n', '    with tab_overview:\n']
for line in else_lines[1:]:
    if line.startswith('    '):
        new_else_lines.append('    ' + line)
    else:
        new_else_lines.append('        ' + line) # Indent the welcome screen into with tab_overview

fallback = """
    with tab_alerts:
        st.info("Carga un archivo de logs en el panel lateral o usa el dataset de muestra para ver las alertas.")
    with tab_root:
        st.info("El análisis de causa raíz aparecerá aquí.")
    with tab_patterns:
        st.info("Los patrones detectados aparecerán aquí.")
    with tab_data:
        st.info("El explorador de eventos estará disponible tras cargar datos.")
"""
new_else_lines.append(fallback)

# Now assemble everything
final_lines = part1 + part2 + new_history_lines + new_else_lines

with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("Modificacion exacta completada")
