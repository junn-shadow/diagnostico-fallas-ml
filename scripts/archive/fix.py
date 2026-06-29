import re

with open("app/dashboard/streamlit_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Busquemos donde se declaran las tabs actualmente
tabs_decl_idx = content.find("tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs")

if tabs_decl_idx != -1:
    print("Found tabs declaration")

# El problema es que en la linea 88 tenemos "with tab_overview:" que esta mal colocado.
# Vamos a restaurar el archivo original desde git si es posible o simplemente arreglarlo manualmente.
