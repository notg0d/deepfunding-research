"""Resolve failed source paths and inspect selected npm files without execution."""
import hashlib
import json
import tarfile

from collect_audit_followups import collect
from collect_audit_sources import AUDIT, SOURCES
from collect_sources import ROOT


def main():
    paths = {
        "dappnode/DAppNode": ["docker-compose.yml", "Dockerfile"],
        "ethereum/eips": ["Gemfile", "EIPS/eip-1.md"],
        "nethermindeth/nethermind": ["Directory.Packages.props"],
        "status-im/nimbus-eth2": ["beacon_chain.nimble", ".gitmodules"],
        "taikoxyz/taiko-mono": ["go.mod"],
        "dappnode/DNP_DAPPMANAGER": ["README.md"],
        "TrueBlocks/trueblocks-core": ["src/README.md", ".gitmodules", "chifra"],
    }
    tasks = [dict(id=repo + ":resolved:" + filename, repo=repo,
                  kind="resolved_repository_source",
                  url="https://raw.githubusercontent.com/" + repo + "/HEAD/" + filename,
                  path=SOURCES / "resolved" / repo.replace("/", "__") / filename)
             for repo, filenames in paths.items() for filename in filenames]
    for repo, directory in [("libp2p/libp2p", ""), ("TrueBlocks/trueblocks-core", "src")]:
        tasks.append(dict(id=repo + ":directory:" + directory, repo=repo,
                          kind="repository_directory_metadata",
                          url="https://api.github.com/repos/" + repo + "/contents/" + directory,
                          path=SOURCES / "roots" / (repo.replace("/", "__") + "__" + (directory or "root") + ".json")))
    index_path = AUDIT / "final_source_index.json"
    existing = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    known = {r["id"] for r in existing if r.get("status") == 200}
    records = [r for r in existing if r["id"] in known] + collect([t for t in tasks if t["id"] not in known])
    (AUDIT / "final_source_index.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    reviewed = {
        "ethereum-cryptography": ["package/package.json", "package/esm/keccak.js", "package/esm/secp256k1.js"],
        "@chainsafe/bls": ["package/package.json", "package/lib/herumi/context.js", "package/lib/blst-native/secretKey.js", "package/lib/blst-native/signature.js"],
        "@tevm/vm": ["package/package.json", "package/src/createBaseVm.js", "package/src/createVm.js"],
        "@tevm/node": ["package/package.json", "package/src/createTevmNode.js"],
        "hardhat-deploy": ["package/package.json"],
        "@shazow/whatsabi": ["package/package.json"],
        "@safe-global/safe-smart-account": ["package/package.json"],
    }
    packages = []
    for package, selected in reviewed.items():
        source = SOURCES / "artifacts" / (package.replace("/", "__") + ".tgz")
        with tarfile.open(source, "r:gz") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            names = [m.name for m in members]
            if package == "hardhat-deploy":
                selected.extend(n for n in names if n.endswith("/index.ts") or n.endswith("/setup.ts"))
            elif package == "@shazow/whatsabi":
                selected.extend(n for n in names if n.endswith("/disasm.ts") or n.endswith("/selectors.ts") or n.endswith("/abi.ts"))
            elif package == "@safe-global/safe-smart-account":
                selected.extend(n for n in names if n.endswith("/Safe.sol"))
            extracted, missing = [], []
            for name in selected:
                if name not in names:
                    missing.append(name)
                    continue
                member = archive.getmember(name)
                if member.size > 250000:
                    raise ValueError("Selected file exceeds review size limit")
                # Explicit selected names only. Do not call extractall or execute package code.
                if ".." in name.split("/") or name.startswith("/"):
                    raise ValueError("Unsafe archive member")
                body = archive.extractfile(member).read()
                target = SOURCES / "artifact_review" / package.replace("/", "__") / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
                extracted.append(dict(member=name, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(),
                                      local_path=target.relative_to(ROOT).as_posix()))
            metadata = json.loads(archive.extractfile("package/package.json").read())
            registry = json.loads((SOURCES / "npm" / (package.replace("/", "__") + ".json")).read_text(encoding="utf-8"))
            def repository_url(value):
                url = value.get("url", "") if isinstance(value, dict) else (value or "")
                return url.removeprefix("git+").removesuffix(".git").rstrip("/")
            packages.append(dict(package=package, version=metadata["version"],
                                 tarball_path=source.relative_to(ROOT).as_posix(),
                                 tarball_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                                 member_names=names, reviewed_files=extracted, missing_selected_files=missing,
                                 identity_and_dependencies_match_registry=all(metadata.get(k) == registry.get(k) for k in ["name", "version", "dependencies", "peerDependencies", "optionalDependencies"]),
                                 normalized_repository_matches_registry=repository_url(metadata.get("repository")) == repository_url(registry.get("repository"))))
    (AUDIT / "artifact_review_index.json").write_text(json.dumps(packages, indent=2), encoding="utf-8")
    print(json.dumps({"additional_sources": len(records), "successful": sum(r.get("status") == 200 for r in records),
                      "artifact_review": [{"package": p["package"], "version": p["version"],
                                           "files": len(p["reviewed_files"]), "missing": p["missing_selected_files"]} for p in packages]}, indent=2))


if __name__ == "__main__":
    main()
