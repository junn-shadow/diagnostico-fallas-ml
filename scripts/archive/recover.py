import json
import re

transcript_path = r"C:\Users\junni\.gemini\antigravity-ide\brain\68a95daa-2bee-48bc-a42e-3efb276e4e3c\.system_generated\logs\transcript.jsonl"

file_content = {}

with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            content_str = str(data) # convert whole json step to string to search
            if 'file:///e:/diagnostico-fallas-ml/app/dashboard/streamlit_app.py' in content_str:
                # Let's extract the exact output block
                # Usually it's in data["content"] or data["tool_calls"] or data["output"]
                def extract_from_dict(d):
                    for k, v in d.items():
                        if isinstance(v, str):
                            if 'file:///e:/diagnostico-fallas-ml/app/dashboard/streamlit_app.py' in v and 'Total Lines: 1160' in v:
                                for l in v.split('\n'):
                                    m = re.match(r'^(\d+):\s(.*)$', l)
                                    if m:
                                        file_content[int(m.group(1))] = m.group(2)
                        elif isinstance(v, dict):
                            extract_from_dict(v)
                        elif isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict):
                                    extract_from_dict(item)
                extract_from_dict(data)
        except Exception:
            pass

if file_content:
    print(f"Recovered {len(file_content)} lines")
    with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
        for i in range(1, 1161):
            if i in file_content:
                f.write(file_content[i] + "\n")
            else:
                f.write("\n")
else:
    print("Could not recover")

