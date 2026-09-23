import json
import re

with open("resources/untranslated_ui.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

valid_strings = []
for s in raw.keys():
    s_clean = s.strip()
    # Filter out code artifacts
    if any(s_clean.startswith(x) for x in ["createElement", ",l)", "e.g.", "http", "./", "../", "0px", "1.", "2.", "3."]):
        continue
    if any(x in s_clean for x in ["createElement", "{", "}", "();", "()=>", "||"]):
        continue
    if len(s_clean) <= 1:
        continue
    if s_clean.isdigit():
        continue
    if s_clean in ["all", "here", "on", "for", "project", "context", "description"]:
        continue
    valid_strings.append(s_clean)

print(f"Total valid UI strings: {len(valid_strings)}")
with open("resources/clean_untranslated_ui.json", "w", encoding="utf-8") as f:
    json.dump(valid_strings, f, ensure_ascii=False, indent=2)
