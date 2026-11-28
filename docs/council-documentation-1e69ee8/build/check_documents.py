#!/usr/bin/env python3
"""Check relative links, rendered assets and pinned source link line ranges."""
import argparse
import json
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

LINK = re.compile(r"\]\(([^\s)]+)\)")
SOURCE = re.compile(r"https://github\.com/tegasae/simple_tickets/(?:blob|tree)/([a-f0-9]{40})/([^#)]+)(?:#L(\d+)(?:-L(\d+))?)?$")
HEADINGS = re.compile(r"^#{1,6}\s+(.+)$", re.M)
CODES = re.compile(r"(?ms)^ *```.*?^ *```\s*$")
USER_PROFILES = ("Обычный сотрудник", "Инженер", "Инженер с правом работы на горячей линии",
                 "Ведущий инженер", "Менеджер", "Руководитель отдела")

def anchors(source):
    explicit = set(re.findall(r"\{#([\w-]+)\}", source))
    for match in HEADINGS.finditer(source):
        value = unicodedata.normalize("NFKC", match[1]).lower()
        value = re.sub(r"[^\w\s-]", "", value).strip().replace(" ", "-")
        explicit.add(value)
    return explicit

@lru_cache(None)
def code_file(snapshot, path):
    filename = snapshot / path
    if filename.is_dir():
        return -1
    return len(filename.read_bytes().splitlines()) if filename.is_file() else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--local", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    snapshots = {
        "1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69": args.published.resolve(),
        "d497e75d4937e8edea98783a5af924c247622e06": args.local.resolve(),
    }
    targets = 0
    unique_source_links = set()
    outside = []
    errors = []
    checked = {}
    documents = sorted(root.rglob("*.md"))
    for file in documents:
        original = file.read_text(encoding="utf-8")
        checked[file] = CODES.sub("", original)
        if re.search(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", original):
            errors.append(f"{file.name}: possible literal credential")
    for file, document in checked.items():
        for href in LINK.findall(document):
            if href.startswith("https://"):
                rule = SOURCE.fullmatch(href)
                if rule and rule[1] in snapshots:
                    unique_source_links.add(href)
                    snapshot, filename = snapshots[rule[1]], unquote(rule[2])
                    length = code_file(snapshot, filename)
                    if length is None:
                        errors.append(f"{file.relative_to(root)}: Missing pinned path {href}")
                    elif rule[3] and not (1 <= int(rule[3]) <= int(rule[4] or rule[3]) <= length):
                        errors.append(f"{file.relative_to(root)}: Invalid line range {href}")
                else:
                    outside.append(href)
                continue
            uri = urlsplit(href)
            if uri.scheme:
                errors.append(f"{file.relative_to(root)}: Non-portable link {href}")
                continue
            target = (file.parent / unquote(uri.path)).resolve() if uri.path else file
            targets += 1
            if not target.is_relative_to(root) or not target.exists():
                errors.append(f"{file.relative_to(root)}: Missing relative target {href}")
            elif uri.fragment and target.suffix == ".md":
                known = anchors(checked.get(target) or target.read_text())
                if unquote(uri.fragment) not in known:
                    errors.append(f"{file.relative_to(root)}: Missing anchor {href}")

    user = (root / "user-guide.md").read_text()
    for profile in USER_PROFILES:
        if not re.search(r"^### " + re.escape(profile) + r"$", user, re.M):
            errors.append(f"Missing user section: {profile}")
    if re.search(r"^\s*```|\b(?:SQL|HTTP|JSON|curl|PATCH|POST)\b", user, re.M):
        errors.append("The user guide contains a technical example")
    svg = sorted((root / "diagrams").glob("*.svg"))
    for image in svg:
        obj = ET.parse(image).getroot()
        if not obj.attrib.get("viewBox") or len(list(obj.iter())) < 9:
            errors.append(f"Unexpected SVG format {image.name}")
        if not image.with_suffix(".dot").exists():
            errors.append(f"Missing DOT source {image.name}")
    if errors:
        raise SystemExit("\n".join(sorted(set(errors))))
    print(json.dumps({"markdown_files":len(documents), "relative_links":targets,
                      "pinned_source_links":len(unique_source_links),
                      "other_external_links":len(set(outside)), "svg_images":len(svg),
                      "user_profiles":len(USER_PROFILES)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
