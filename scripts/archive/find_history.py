import os
import re
import glob

history_dir = r"C:\Users\junni\AppData\Roaming\Code\User\History"

best_file = None
max_lines = 0

if os.path.exists(history_dir):
    for root, dirs, files in os.walk(history_dir):
        for file in files:
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(' in content:
                        lines = content.count('\n')
                        if lines > max_lines:
                            max_lines = lines
                            best_file = filepath
            except Exception:
                pass

if best_file:
    print(f"Found best file {best_file} with {max_lines} lines")
    import shutil
    shutil.copy2(best_file, "app/dashboard/streamlit_app_recovered.py")
else:
    print("Not found in VS Code history")
