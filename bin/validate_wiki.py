#!/usr/bin/env python3
"""Validate wiki-local Markdown image targets and wikilink targets."""

import argparse
import os
import re
import sys


WIKI_DIR = "wiki"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def markdown_files():
    for root, _, files in os.walk(WIKI_DIR):
        for name in files:
            if name.endswith(".md"):
                yield os.path.join(root, name)


def page_targets():
    targets = set()
    for path in markdown_files():
        targets.add(os.path.splitext(os.path.basename(path))[0])
    return targets


def validate_images():
    errors = []
    for page in markdown_files():
        page_dir = os.path.dirname(page)
        with open(page, encoding="utf-8") as fh:
            content = fh.read()
        for raw_target in IMAGE_RE.findall(content):
            target = raw_target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "data:")):
                continue
            resolved = os.path.normpath(os.path.join(page_dir, target))
            if not os.path.isfile(resolved):
                errors.append(f"{page}: missing image {raw_target}")
    return errors


def validate_wikilinks():
    targets = page_targets()
    errors = []
    for page in markdown_files():
        with open(page, encoding="utf-8") as fh:
            content = fh.read()
        for target in WIKILINK_RE.findall(content):
            target = target.strip()
            if target.startswith(("http://", "https://")):
                continue
            target = target.rsplit("/", 1)[-1].removesuffix(".md")
            if target not in targets:
                errors.append(f"{page}: missing wikilink target [[{target}]]")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-only", action="store_true")
    args = parser.parse_args()
    errors = validate_images()
    if not args.images_only:
        errors.extend(validate_wikilinks())
    if errors:
        for error in errors:
            print(error)
        print(f"Validation failed: {len(errors)} issue(s)")
        return 1
    print("Wiki validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
