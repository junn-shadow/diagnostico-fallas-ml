import json

transcript_path = r"C:\Users\junni\.gemini\antigravity-ide\brain\68a95daa-2bee-48bc-a42e-3efb276e4e3c\.system_generated\logs\transcript.jsonl"

with open(transcript_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "Total Lines: 1160" in line:
        print(f"Found at {idx}")
        with open(f"step_{idx}.json", "w", encoding="utf-8") as out:
            out.write(line)

