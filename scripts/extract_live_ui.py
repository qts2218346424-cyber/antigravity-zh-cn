import urllib.request
import ssl
import json
import re
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 自动发现活动端口
url = None
port = None
# 查 65106 上的 json/list
try:
    req = urllib.request.Request('http://127.0.0.1:65106/json/list', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=2) as r:
        tabs = json.loads(r.read().decode('utf-8'))
    for t in tabs:
        u = t.get('url', '')
        if '127.0.0.1' in u:
            m = re.search(r'https?://127\.0\.0\.1:(\d+)', u)
            if m:
                port = int(m.group(1))
                break
except Exception as e:
    print('Failed to query devtools list:', e)

if not port:
    port = 53312

url = f'https://127.0.0.1:{port}/main.js'
print(f'Fetching live main.js from: {url}')

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
    data = r.read().decode('utf-8', errors='ignore')

print(f'Fetched main.js length: {len(data):,} bytes')

# 提取 UI 词条
labels = re.findall(r'label:\s*"([^"]{2,80})"', data)
labels += re.findall(r"label:\s*'([^']{2,80})'", data)
tooltips = re.findall(r'tooltip:\s*"([^"]{2,80})"', data)
tooltips += re.findall(r"tooltip:\s*'([^']{2,80})'", data)
placeholders = re.findall(r'placeholder:\s*"([^"]{2,80})"', data)
placeholders += re.findall(r"placeholder:\s*'([^']{2,80})'", data)
titles = re.findall(r'title:\s*"([^"]{2,80})"', data)
titles += re.findall(r"title:\s*'([^']{2,80})'", data)
jsx_texts = re.findall(r'>([A-Z][A-Za-z0-9\s,\.\?\!\'\-]{2,50})<', data)
button_texts = re.findall(r'["\']([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){1,5})["\']', data)

all_strings = set(labels + tooltips + placeholders + titles + jsx_texts + button_texts)
clean_strings = set()
for s in all_strings:
    s = s.strip()
    if (len(s) >= 2 
        and not s.startswith('http') 
        and not s.startswith('/') 
        and not s.startswith('.')
        and not s.startswith('{')
        and not s.startswith('var ')
        and not s.startswith('const ')
        and not s.endswith('.js')
        and not s.endswith('.css')
        and not s.endswith('.png')
        and not s.endswith('.svg')
        and not re.search(r'^[a-z]+[A-Z]', s) # 排除驼峰变量名
        and not re.search(r'^[a-z_0-9]+$', s) # 排除纯小写标识符
        and any(c.isalpha() for c in s)):
        clean_strings.add(s)

dict_path = Path(r'e:\antigravity-cn\resources\antigravity-zh-CN.json')
with open(dict_path, 'r', encoding='utf-8') as f:
    current_dict = json.load(f)

lower_dict = {k.lower(): v for k, v in current_dict.items()}

untranslated = sorted([s for s in clean_strings if s not in current_dict and s.lower() not in lower_dict])
print(f'Total clean UI candidate strings: {len(clean_strings)}')
print(f'Already in dictionary: {len(clean_strings) - len(untranslated)}')
print(f'Untranslated: {len(untranslated)}')

out_path = Path(r'e:\antigravity-cn\resources\untranslated_live.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(untranslated, f, ensure_ascii=False, indent=2)

print(f'Saved to {out_path}')
