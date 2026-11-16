"""Print relevant fragments of the public market client without executing it."""
from pathlib import Path
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

path = next((Path(__file__).resolve().parent / "sources" / "market").glob("index-*.js"))
text = path.read_text(encoding="utf-8")
urls = sorted(set(re.findall(r'https?://[^\s"<>`\\]{8,160}', text)))
print("RELEVANT URLS")
for url in urls:
    if any(word in url.lower() for word in ("seer", "subgraph", "graph", "optimism", "api.", "deepfund", "supabase")):
        print(url)
print("CLIENT FRAGMENTS")
for pattern in (r"get-originality-r3-v3-markets-data", r"N5=", r"functions/", r"supabase", r"fetch\(", r"subgraph", r"apiEndpoint", r"\.netlify/functions", r"volume", r"liquidity"):
    matches = list(re.finditer(pattern, text, re.I))
    print("\nPATTERN", pattern, "COUNT", len(matches))
    for match in matches[:8]:
        print(text[max(0, match.start() - 240):match.end() + 500])
