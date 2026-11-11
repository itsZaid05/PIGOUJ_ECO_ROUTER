"""Inspect an available release, never import or install its GPU runtime."""

import argparse
import ast
import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="0.33.0")
    parser.add_argument("--expected-commit", default="4ba787ec9959e566d3b587a796dff07673324da5")
    args = parser.parse_args()
    release = json.loads(fetch(f"https://pypi.org/pypi/vllm/{args.version}/json"))
    version = release["info"]["version"]
    tag = f"v{version}"
    ref = json.loads(fetch(f"https://api.github.com/repos/vllm-project/vllm/git/ref/tags/{tag}"))
    obj = ref["object"]
    while obj["type"] == "tag":
        obj = json.loads(fetch(obj["url"]))["object"]
    commit = obj["sha"]
    if commit != args.expected_commit:
        raise ValueError(f"release source mismatch: expected {args.expected_commit}, got {commit}")
    records = []
    paths = (
        "vllm/v1/core/kv_cache_manager.py",
        "vllm/v1/core/sched/scheduler.py",
        "vllm/v1/engine/core.py",
        "vllm/v1/engine/async_llm.py",
        "vllm/entrypoints/openai/api_server.py",
    )
    root = Path("artifacts/validation/vllm_source")
    root.mkdir(parents=True, exist_ok=True)
    license_url = f"https://raw.githubusercontent.com/vllm-project/vllm/{commit}/LICENSE"
    license_text = fetch(license_url)
    (root / "LICENSE").write_bytes(license_text)
    for path in paths:
        url = f"https://raw.githubusercontent.com/vllm-project/vllm/{commit}/{path}"
        raw = fetch(url)
        (root / path.replace("/", "__")).write_bytes(raw)
        tree = ast.parse(raw)
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in (
                    "allocate_slots",
                    "add_request",
                    "schedule",
                    "generate",
                    "try_admit",
                    "attempt_admission",
                ):
                    methods.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "signature": ast.unparse(node.args),
                        }
                    )
        records.append(
            {
                "path": path,
                "url": url,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "methods": methods,
                "try_admit_occurrences": raw.count(b"try_admit"),
                "expected_epoch_occurrences": raw.count(b"expected_epoch"),
            }
        )
    print(
        json.dumps(
            {
                "recorded_at_utc": datetime.now(UTC).isoformat(),
                "pypi_version": version,
                "tag": tag,
                "source_commit": commit,
                "installed": False,
                "execution_verified": False,
                "license_url": license_url,
                "license_sha256": hashlib.sha256(license_text).hexdigest(),
                "files": records,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
