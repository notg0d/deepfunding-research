"""Make bounded excerpts for documentation-level review, retaining source links."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
index = json.loads((root / "sources" / "repository_index.json").read_text(encoding="utf-8"))
lines = []
for item in index:
    path = Path(item["path"])
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    cleaned = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', cleaned)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    lines.extend(["", "REPOSITORY: " + item["repo"], "SOURCE: " + item["source"]["url"], "SUMMARY: " + cleaned[:1150]])
    candidates = list(re.finditer(r"\b(fork(?:ed)?|wrapper|depends? on|dependencies|based on|built on|built with|powered by|arkworks|plonky3|kurtosis|ethereumjs|libff|blst|mcl|revm|upstream)\b", cleaned, re.I))
    shown = []
    for match in candidates:
        if any(abs(match.start() - prior) < 200 for prior in shown):
            continue
        shown.append(match.start())
        lines.append("EVIDENCE: " + cleaned[max(0, match.start()-100):match.end()+200])
        if len(shown) >= 3:
            break
(root / "sources" / "repository_digest.txt").write_text("\n".join(lines), encoding="utf-8")
print("Created digest for", len(index), "repositories")
