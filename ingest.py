#!/usr/bin/env python3
"""
LLM Wiki Ingest Script — single-file mode
Processes one uningested file at a time to keep token costs low.
"""

import os
import re
import shutil
import json
import requests
import subprocess
from datetime import datetime, timezone

# ── Config (template-friendly) ───────────────────────────────
API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = os.environ.get("MODEL", "deepseek/deepseek-v4-pro")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

RAW_DIR = os.environ.get("RAW_DIR", "raw")
WIKI_DIR = os.environ.get("WIKI_DIR", "wiki")
INDEX_FILE = os.environ.get("INDEX_FILE", "index.md")
LOG_FILE = os.environ.get("LOG_FILE", "log.md")
AGENTS_FILE = os.environ.get("AGENTS_FILE", "AGENTS.md")
PROMPT_FILE = os.environ.get("PROMPT_FILE", "prompt.txt")

CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


config = load_config()

PROJECT_NAME = os.environ.get("PROJECT_NAME", config.get("PROJECT_NAME", "LLM Wiki"))
DOMAIN = os.environ.get("DOMAIN", config.get("DOMAIN", "General"))
MODEL = os.environ.get("MODEL", config.get("MODEL", MODEL))
STRICT_MODE = config.get("STRICT_MODE", False)


def api_call(system_prompt, user_message, temperature=0.4):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": 8000,
    }
    response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def get_ingested_files():
    ingested = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            for line in f:
                if "Ingested" in line and ":" in line:
                    parts = line.split("Ingested ")[1] if "Ingested " in line else ""
                    for name in parts.split(","):
                        name = name.strip().strip(".")
                        if name:
                            ingested.add(name)
    return ingested


def get_next_file():
    ingested = get_ingested_files()
    if os.path.exists(RAW_DIR):
        for f in sorted(os.listdir(RAW_DIR)):
            # support txt, md, and basic text-extracted docs
            if (f.endswith(".txt") or f.endswith(".md")) and f not in ingested:
                return os.path.join(RAW_DIR, f)
    return None


def read_schema():
    if os.path.exists(AGENTS_FILE):
        with open(AGENTS_FILE) as f:
            return f.read()
    return ""


def read_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE) as f:
            return f.read()
    return ""


def read_prompt_template():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE) as f:
            return f.read()
    raise FileNotFoundError("prompt.txt not found")


# Only wiki/ markdown pages may be created/updated via model output.
# index.md and log.md are handled by dedicated fields, not arbitrary paths.
SAFE_PATH_RE = re.compile(r"^wiki/[a-z0-9][a-z0-9\-/]*\.md$")


def assert_safe_path(p):
    """Reject any path that isn't a wiki/*.md file. Prevents prompt-injection
    driven writes to .github/, ingest.py, AGENTS.md, etc."""
    if not isinstance(p, str) or not SAFE_PATH_RE.match(p):
        raise ValueError(f"Refusing unsafe path: {p!r}")
    parts = p.split("/")
    if ".." in parts or ".git" in parts:
        raise ValueError(f"Path traversal or hidden segment blocked: {p!r}")
    return p


def apply_changes(response_text):
    json_str = response_text
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0]
    
    # Find outermost braces
    start = json_str.find('{')
    end = json_str.rfind('}')
    if start >= 0 and end > start:
        json_str = json_str[start:end+1]
    
    changes = json.loads(json_str)
    written = []
    rejected = []

    for f in changes.get("files_to_create", []):
        try:
            path = assert_safe_path(f["path"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write(f["content"])
            print(f"  Created: {path}")
            written.append(path)
        except (ValueError, KeyError) as e:
            rejected.append((f.get("path", "<missing>"), str(e)))
            print(f"  REJECTED create {f.get('path', '<missing>')}: {e}")
    
    for f in changes.get("files_to_update", []):
        try:
            path = assert_safe_path(f["path"])
            with open(path, "w") as fh:
                fh.write(f["content"])
            print(f"  Updated: {path}")
            written.append(path)
        except (ValueError, KeyError) as e:
            rejected.append((f.get("path", "<missing>"), str(e)))
            print(f"  REJECTED update {f.get('path', '<missing>')}: {e}")
    
    if changes.get("index_md"):
        # Backup before overwrite so a poisoned index can be rolled back.
        if os.path.exists(INDEX_FILE):
            shutil.copyfile(INDEX_FILE, INDEX_FILE + ".bak")
        with open(INDEX_FILE, "w") as fh:
            fh.write(changes["index_md"])
        print(f"  Updated: {INDEX_FILE} (backup at {INDEX_FILE}.bak)")
    
    if changes.get("log_entry"):
        with open(LOG_FILE, "a") as fh:
            fh.write(changes["log_entry"] + "\n")
        print(f"  Logged: {changes['log_entry']}")
    
    if rejected:
        print(f"  ⚠ {len(rejected)} path(s) rejected as unsafe — see above.")
    
    return changes.get("summary", "")


def git_commit_and_push(summary):
    subprocess.run(["git", "config", "--local", "user.name", "Wiki Ingest Bot"], check=True)
    subprocess.run(["git", "config", "--local", "user.email", "bot@wiki.local"], check=True)
    subprocess.run(["git", "add", "wiki/", "index.md", "log.md"], check=True)
    
    result = subprocess.run(["git", "diff", "--staged", "--quiet"], capture_output=True)
    if result.returncode == 0:
        print("No changes to commit.")
        return
    
    subprocess.run(["git", "commit", "-m", f"Ingest: {summary}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Committed and pushed.")


def detect_orphans():
    """Scan wiki/ for pages with zero incoming [[wikilinks]]."""
    pages = {}

    # collect all pages
    for root, _, files in os.walk(WIKI_DIR):
        for f in files:
            if f.endswith(".md"):
                name = f.replace(".md", "")
                pages[name] = 0

    # count inbound links
    for root, _, files in os.walk(WIKI_DIR):
        for f in files:
            if f.endswith(".md"):
                with open(os.path.join(root, f)) as fh:
                    content = fh.read()
                    for name in pages.keys():
                        if f"[[{name}]]" in content:
                            pages[name] += 1

    # ignore self-links (rough but fine for now)
    orphans = [name for name, count in pages.items() if count == 0]

    if orphans:
        print("\nWARNING: Orphan pages detected:")
        for o in orphans:
            print(f"  - {o}")
        if STRICT_MODE:
            raise RuntimeError("Orphan pages detected in strict mode")
    else:
        print("No orphan pages detected.")

    return orphans


def main():
    print("=== LLM Wiki Ingest (single-file mode) ===")
    
    filepath = get_next_file()
    if not filepath:
        print("No new files to ingest. Done.")
        return
    
    print(f"Ingesting: {filepath}")
    
    schema = read_schema()
    index_content = read_index()
    
    with open(filepath) as f:
        source_text = f.read()

    # --- Safety: truncate very large files to control cost ---
    # 50k chars ≈ 12k tokens, fine for deepseek-chat (~$0.01/file).
    # Raises the default 20k because real research reports exceed it.
    MAX_CHARS = int(os.environ.get("MAX_CHARS", 50000))
    if len(source_text) > MAX_CHARS:
        source_text = source_text[:MAX_CHARS]
        print(f"Truncated input to {MAX_CHARS} characters")
    
    template = read_prompt_template()
    prompt = template.format(
        PROJECT_NAME=PROJECT_NAME,
        DOMAIN=DOMAIN,
        SCHEMA=schema,
        INDEX=index_content,
        SOURCE=source_text,
    )

    print(f"Calling {MODEL}...")
    response = api_call(
        system_prompt="You are a precise wiki compiler. Output valid JSON exactly as requested. Use [[wikilinks]] for cross-references.",
        user_message=prompt,
        temperature=0.3
    )
    
    print("Applying changes...")
    summary = apply_changes(response)
    
    print(f"Summary: {summary}")

    # Post-pass: detect orphan pages before commit
    orphans = detect_orphans()
    
    git_commit_and_push(summary)
    print("Done!")


if __name__ == "__main__":
    main()
