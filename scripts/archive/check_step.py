import json

with open("step_209.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(data.keys())
print(data.get("type"))
if "content" in data:
    print(data["content"][:200])

