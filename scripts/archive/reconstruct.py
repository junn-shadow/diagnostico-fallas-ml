import json
import re

transcript_path = r"C:\Users\junni\.gemini\antigravity-ide\brain\68a95daa-2bee-48bc-a42e-3efb276e4e3c\.system_generated\logs\transcript.jsonl"
file_content = {}

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("type") == "VIEW_FILE":
                content = data.get("content", "")
                if 'file:///e:/diagnostico-fallas-ml/app/dashboard/streamlit_app.py' in content and 'Total Lines: 1160' in content:
                    for l in content.split('\n'):
                        m = re.match(r'^(\d+):\s(.*)$', l)
                        if m:
                            file_content[int(m.group(1))] = m.group(2)
        except Exception:
            pass

if file_content:
    print(f"Recovered {len(file_content)} lines!")
    with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
        for i in range(1, 1161):
            if i in file_content:
                f.write(file_content[i] + "\n")
            else:
                f.write("\n")
else:
    print("Failed to recover")
