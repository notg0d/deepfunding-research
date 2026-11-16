"""Extract declared dependencies and metadata for research review."""
import json
from pathlib import Path
import re
import tomllib

root = Path(__file__).resolve().parent / "sources" / "repositories"
lines = []
for folder in sorted(root.iterdir()):
    files = [p for p in folder.rglob("*") if p.is_file() and not p.name.endswith(".source.json") and p.name not in ("README.md", "README.rst", "readme.md", "README", "Readme.md")]
    if not files:
        continue
    lines.extend(["", "REPOSITORY: " + folder.name.replace("__", "/")])
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        label = str(path.relative_to(folder))
        if path.name == "github_metadata.json":
            d = json.loads(text)
            value = {k: d.get(k) for k in ("full_name", "description", "fork", "archived", "pushed_at", "default_branch")}
            value["parent"] = (d.get("parent") or {}).get("full_name")
            value["source"] = (d.get("source") or {}).get("full_name")
            lines.append(label + ": " + json.dumps(value, ensure_ascii=False))
        elif path.suffix == ".toml":
            try:
                d = tomllib.loads(text)
                package = d.get("package", {}).get("name", d.get("project", {}).get("name", "workspace"))
                dependencies = d.get("dependencies", d.get("workspace", {}).get("dependencies", d.get("project", {}).get("dependencies", [])))
                if isinstance(dependencies, dict):
                    deps = []
                    for k,v in dependencies.items():
                        if isinstance(v, dict):
                            v = {a:b for a,b in v.items() if a in ("git", "path", "version")}
                        deps.append(k + "=" + str(v))
                    dependency_text = "; ".join(deps)
                else:
                    dependency_text = "; ".join(dependencies)
                lines.append(label + ": " + str(package) + " DEPENDENCIES: " + dependency_text[:3000])
            except Exception:
                lines.append(label + ": " + text[:900].replace("\n", " "))
        elif path.name == "package.json":
            d = json.loads(text)
            lines.append(label + ": " + str(d.get("name")) + " RUNTIME: " + json.dumps(d.get("dependencies", {}))[:2000] + " PEER: " + json.dumps(d.get("peerDependencies", {}))[:700])
        elif path.name == "go.mod":
            names = re.findall(r"^\s*([^\s]+) v[^\s]+", text, re.M)
            critical = [n for n in names if any(t in n.lower() for t in ("ethereum", "flashbots", "crate-crypto", "wealdtech", "herumi", "consensys", "supranational", "nethermind", "gnark", "libp2p"))]
            lines.append(label + ": " + text.splitlines()[0] + " SELECTED DEPENDENCIES: " + "; ".join(critical))
        elif path.name == "src/README.md" or label == "src\\README.md":
            lines.append(label + ": " + re.sub(r'\s+', ' ', re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text))[:1500])
        else:
            snippets = []
            for pattern in (r"import[^\n]+", r"from[^\n]+", r"github\.com/[^\s]+", r"image:[^\n]+", r"mcl[^\n]*", r"revm[^\n]*", r"py-evm[^\n]*", r"ethereum-lists[^\n]*"):
                snippets.extend(re.findall(pattern, text, re.I)[:5])
            lines.append(label + ": " + " | ".join(snippets)[:1500])
(root.parent / "extra_digest.txt").write_text("\n".join(lines), encoding="utf-8")
print("Created extra digest")
