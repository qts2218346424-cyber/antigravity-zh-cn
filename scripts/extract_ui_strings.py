import re
import json

with open("bundle_main.js", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

# Let's find all string literals in React createElement or JSX-like structures
# e.g., createElement("...", ..., "string") or title: "...", label: "...", description: "..."
patterns = [
    r'title:\s*"([^"]{2,100})"',
    r'label:\s*"([^"]{2,100})"',
    r'description:\s*"([^"]{2,200})"',
    r'shortDescription:\s*"([^"]{2,200})"',
    r'longDescription:\s*"([^"]{2,300})"',
    r'displayName:\s*"([^"]{2,100})"',
    r'placeholder:\s*"([^"]{2,100})"',
    r'tooltip:\s*"([^"]{2,100})"',
    r'aria-label":\s*`([^`]{2,100})`',
    r'aria-label":\s*"([^"]{2,100})"',
    r'createElement\([a-zA-Z0-9_\.]+,null,"([^"]{2,100})"\)',
    r'createElement\("span",\{[^}]*\},"([^"]{2,100})"\)',
    r'createElement\("div",\{[^}]*\},"([^"]{2,100})"\)',
    r'createElement\("p",\{[^}]*\},"([^"]{2,100})"\)',
    r'createElement\("h[1-6]",\{[^}]*\},"([^"]{2,100})"\)',
    r'createElement\("button",\{[^}]*\},"([^"]{2,100})"\)',
]

found = set()
for p in patterns:
    for m in re.finditer(p, text):
        val = m.group(1).strip()
        if re.search(r'^[A-Za-z0-9\s,\.\?\!\'\-\+\(\)\:\;\/]{2,}$', val):
            if not val.startswith("var ") and not val.startswith("return ") and not val.startswith("http"):
                found.add(val)

# Also check existing dictionary
with open("resources/antigravity-zh-CN.json", "r", encoding="utf-8") as f:
    cn_dict = json.load(f)

untranslated = sorted([s for s in found if s not in cn_dict])
print(f"Total extracted strings matching UI patterns: {len(found)}")
print(f"Untranslated strings count: {len(untranslated)}")

with open("resources/untranslated_ui.json", "w", encoding="utf-8") as f:
    json.dump({s: "" for s in untranslated}, f, ensure_ascii=False, indent=2)

print("Saved to resources/untranslated_ui.json")
