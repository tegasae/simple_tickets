#!/usr/bin/env python3
"""Render the two complete Markdown documents with one title/TOC template."""
import argparse
import io
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote, unquote, urlsplit

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, NameObject, NumberObject, TextStringObject
from weasyprint import HTML

DEFAULT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "1e69ee8a6368d8bd1bf9971e4a7501f879e2cf69"
PREPARATION_DATE = "28 ноября 2026"


def portable_links(data, output, root):
    writer = PdfWriter(clone_from=io.BytesIO(data))
    writer.pdf_header = data.partition(b"\n")[0].decode("ascii")
    for page in writer.pages:
        for reference in page.get("/Annots", []):
            action = reference.get_object().get("/A")
            if action is None or action.get("/S") != "/URI":
                continue
            uri = urlsplit(str(action.get("/URI", "")))
            if uri.scheme != "file":
                continue
            target = Path(unquote(uri.path)).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Link outside the bundle: {target}")
            relative = target.relative_to(root)
            if relative.as_posix() in {"backend.md", "user-guide.md"}:
                action.clear()
                action[NameObject("/S")] = NameObject("/GoToR")
                action[NameObject("/F")] = TextStringObject(relative.with_suffix(".pdf").as_posix())
                action[NameObject("/D")] = (
                    TextStringObject(unquote(uri.fragment)) if uri.fragment else
                    ArrayObject([NumberObject(0), NameObject("/Fit")])
                )
            else:
                suffix = ("#" + uri.fragment) if uri.fragment else ""
                action[NameObject("/URI")] = TextStringObject(quote(relative.as_posix()) + suffix)
    with TemporaryDirectory(prefix=".print-", dir=output.parent) as temporary:
        working = Path(temporary) / output.name
        with working.open("wb") as target:
            writer.write(target)
        working.replace(output)


def render(root, name, binary):
    markdown = (root / (name + ".md")).read_text(encoding="utf-8")
    title, separator, body = markdown.partition("\n")
    if not separator or not title.startswith("# "):
        raise ValueError(f"First line of {name}.md must be a level-one heading")
    arguments = [
        binary, "--from=markdown", "--to=html5", "--standalone",
        "--toc", "--toc-depth=2", "--shift-heading-level-by=-1",
        "--template", str(root / "build" / "template.html"),
        "--css", "build/print.css", "--metadata", "lang=ru",
        "--metadata", f"title={title[2:]}",
        "--metadata", f"snapshot={BASE_COMMIT}",
        "--metadata", f"date={PREPARATION_DATE}",
        "--metadata", "audience=" + (
            "Техническая документация Simple Tickets" if name == "backend"
            else "Рабочие процессы, роли и статусы"
        ),
    ]
    html = subprocess.check_output(arguments, input=body, text=True, cwd=root)
    data = HTML(string=html, base_url=root.as_uri() + "/").write_pdf(pdf_tags=True)
    portable_links(data, root / (name + ".pdf"), root)
    print(root / (name + ".pdf"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT)
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("documents", nargs="*", default=["backend", "user-guide"])
    args = parser.parse_args()
    for name in args.documents:
        if name not in {"backend", "user-guide"}:
            parser.error("documents must be backend or user-guide")
        render(args.root.resolve(), name, args.pandoc)


if __name__ == "__main__":
    main()
