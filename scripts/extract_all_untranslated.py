import urllib.request
import ssl
import re
import json
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://127.0.0.1:60651/main.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
    data = r.read().decode('utf-8', errors='ignore')

labels = re.findall(r'label:"([^"]{2,60})"', data)
tooltips = re.findall(r'tooltip:"([^"]{2,60})"', data)
placeholders = re.findall(r'placeholder:"([^"]{2,60})"', data)
titles = re.findall(r'title:"([^"]{2,60})"', data)
# Also buttons or headings in React: text between > and < in jsx
jsx_texts = re.findall(r'>([A-Z][A-Za-z0-9\s,\.\?\!\'\-]{2,40})<', data)

all_strings = set(labels + tooltips + placeholders + titles + jsx_texts)
clean_strings = set()
for s in all_strings:
    s = s.strip()
    if (len(s) >= 2 
        and not s.startswith("http") 
        and not s.startswith("/") 
        and not s.startswith(".")) :
        clean_strings.add(s)

dict_path = Path(r'e:\antigravity-cn\resources\antigravity-zh-CN.json')
with open(dict_path, 'r', encoding='utf-8') as f:
    current_dict = json.load(f)

untranslated = sorted([s for s in clean_strings if s not in current_dict])
print(f"Total clean strings found: {len(clean_strings)}")
print(f"Already in dictionary: {len(clean_strings) - len(untranslated)}")
print(f"Untranslated: {len(untranslated)}")

with open(r'e:\antigravity-cn\resources\untranslated_all.json', 'w', encoding='utf-8') as f:
    json.dump(untranslated, f, ensure_ascii=False, indent=2)

print("Saved untranslated list to resources/untranslated_all.json")
