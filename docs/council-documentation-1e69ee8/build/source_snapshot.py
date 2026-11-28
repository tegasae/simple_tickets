#!/usr/bin/env python3
"""Freeze the documentation evidence set and record worktree/index metadata."""
import argparse
import hashlib
import io
import json
import os
import stat
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

TEXT = {".md", ".rst", ".py", ".sh", ".txt", ".ini", ".cfg", ".toml", ".yaml",
        ".yml", ".json", ".patch", ".sql", ".dot", ".mmd", ".service"}
EXCLUDED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
FRONTENDS = {"react", "simple_tickets_frontend_v2"}
SOFTWARE_ROOTS = {"src", "utils", "scripts", "tests", "tests_pyramid",
                  "dockerfiles", "db", "db-docker", "docs", "reviews"}
ROOT_CONFIG = {".gitignore", ".dockerignore", ".dockignore", ".coveragerc",
               "Dockerfile", "Pipfile", "Makefile", "uv.lock", ".python-version"}

def include(name):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts
            or any(part in EXCLUDED_PARTS or part.lower().startswith(".env")
                   or part.startswith("council-documentation-") for part in path.parts)):
        return False
    if path.parts[0] in FRONTENDS or path.suffix in {".db", ".sqlite", ".sqlite3"}:
        return False
    if "package-lock" in path.name or "credential" in path.name.lower():
        return False
    if any(part in {"secrets", "credentials"} for part in path.parts):
        return False
    # The repository also ships data dumps with .sql extensions.
    if path.suffix == ".sql" and path.as_posix() != "db/schema.sql":
        return False
    if len(path.parts) == 1:
        return path.suffix in TEXT or path.name in ROOT_CONFIG
    return path.parts[0] in SOFTWARE_ROOTS and (
        path.suffix in TEXT or path.name.startswith("Dockerfile")
    )

def git(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )

def filename_list(raw):
    return [os.fsdecode(item) for item in raw.split(b"\0") if item]

def save_manifest(records, output):
    data = (json.dumps(records, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")
    output.write_bytes(data)
    return hashlib.sha256(data).hexdigest()

def remember_file(destination, name, data, executable):
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    target.chmod(0o755 if executable else 0o644)
    return {"path":name, "executable":executable,
            "sha256":hashlib.sha256(data).hexdigest()}

def capture_local(repo, out):
    out.mkdir(parents=True, exist_ok=True)
    status = git(repo, "status", "--short", "--branch", "--untracked-files=all")
    stage = git(repo, "ls-files", "--stage", "-z")
    tracked = git(repo, "ls-files", "--cached", "-z")
    extra = git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    branch = git(repo, "branch", "--show-current").decode().strip() or "detached HEAD"
    index_path = Path(os.fsdecode(git(repo, "rev-parse", "--git-path", "index").strip()))
    if not index_path.is_absolute():
        index_path = repo / index_path
    index_hash = hashlib.sha256(index_path.read_bytes()).hexdigest()
    records = []
    for name in sorted(set(filename_list(tracked) + filename_list(extra))):
        if not include(name):
            continue
        path = repo / name
        if path.is_symlink():
            records.append({"path": name, "state": "symlink excluded"})
        elif not path.is_file():
            records.append({"path": name, "state": "missing"})
        else:
            records.append(remember_file(out / "local", name, path.read_bytes(),
                                         bool(path.stat().st_mode & stat.S_IXUSR)))
    evidence = {"root": str(repo), "branch": branch, "head": head,
                "status_sha256": hashlib.sha256(status).hexdigest(),
                "stage_sha256": hashlib.sha256(stage).hexdigest(), "index_sha256": index_hash,
                "worktree_sha256": save_manifest(records, out / "local-manifest.json"),
                "evidence_files": len(records)}
    (out / "local-status.txt").write_bytes(status)
    (out / "local.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence

def capture_commit(repo, revision, out):
    names = filename_list(git(repo, "ls-tree", "-r", "--name-only", "-z", revision))
    paths = sorted(set(name for name in names if include(name)))
    archive = git(repo, "archive", "--format=tar", revision, "--", *paths)
    records = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            if member.isfile() and include(member.name):
                records.append(remember_file(out / "published", member.name,
                                             source.extractfile(member).read(),
                                             bool(member.mode & stat.S_IXUSR)))
    records.sort(key=lambda item: item["path"])
    evidence = {"head":revision, "snapshot_sha256": save_manifest(records, out / "published-manifest.json"),
                "evidence_files":len(records)}
    (out / "published.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--commit", help="Capture this revision instead of the worktree")
    args = parser.parse_args()
    print(json.dumps(capture_commit(args.repo.resolve(), args.commit, args.out)
                     if args.commit else capture_local(args.repo.resolve(), args.out), indent=2))
