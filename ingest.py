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
MODEL = os.environ.get("MODEL", "qwen/qwen3-235b-a22b-thinking-2507")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

RAW_DIR = os.environ.get("RAW_DIR", "raw")
WIKI_DIR = os.environ.get("WIKI_DIR", "wiki")
INDEX_FILE = os.environ.get("INDEX_FILE", "wiki/index.md")
LOG_FILE = os.environ.get("LOG_FILE", "wiki/log.md")
AGENTS_FILE = os.environ.get("AGENTS_FILE", "AGENTS.md")
INGESTED_TRACKER = os.path.join(WIKI_DIR, ".ingested.json")
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
        "max_tokens": 32000,
    }
    response = requests.post(API_URL, headers=headers, json=payload, timeout=600)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def get_ingested_files():
    ingested = set()
    if os.path.exists(INGESTED_TRACKER):
        try:
            with open(INGESTED_TRACKER) as f:
                data = json.load(f)
            if isinstance(data, list):
                ingested = set(data)
        except (json.JSONDecodeError, OSError):
            print(f"  Warning: could not read {INGESTED_TRACKER}, treating as empty")
    return ingested


def mark_as_ingested(filenames):
    ingested = get_ingested_files()
    for name in filenames:
        ingested.add(os.path.basename(name))
    os.makedirs(os.path.dirname(INGESTED_TRACKER), exist_ok=True)
    with open(INGESTED_TRACKER, "w") as f:
        json.dump(sorted(ingested), f, indent=2)
    print(f"  Tracked {len(filenames)} file(s) as ingested ({len(ingested)} total)")


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


def repair_json(s):
    """Best-effort repair of common LLM JSON errors. Tuned for the
    'Expecting ',' delimiter' error the batch ingest hits."""
    # Strip non-JSON prefix/suffix — some models add explanatory text
    # outside the backtick block even when instructed not to.
    start = s.find('{')
    end = s.rfind('}')
    if start >= 0 and end > start:
        s = s[start:end+1]
    # Remove trailing commas before ] or }
    s = re.sub(r',(\s*[}\]])', r'\1', s)
    # Add missing comma between adjacent object-braces in an array
    s = re.sub(r'\}\s*\{', '},{', s)
    return s


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
    
    try:
        changes = json.loads(json_str)
    except json.JSONDecodeError:
        print("  JSON parse error, attempting repair...")
        json_str = repair_json(json_str)
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
        # Sync sub-index pages (skills/index.md, etc.) from index_md
        sync_subindex_pages(changes["index_md"])
    
    if changes.get("log_entry"):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        line = changes["log_entry"].strip()
        # Replace any LLM-generated date (e.g. "2026-06-28: ...") with actual date
        if re.match(r"^\d{4}-\d{2}-\d{2}:", line):
            line = line[11:].strip()
        line = f"{today}: {line}"
        with open(LOG_FILE, "a") as fh:
            fh.write(line + "\n")
        print(f"  Logged: {line}")
    
    # Sync sources page and figures catalog after every ingest
    sync_sources_page()
    sync_figures_page()
    
    if rejected:
        print(f"  ⚠ {len(rejected)} path(s) rejected as unsafe — see above.")
    
    return changes.get("summary", "")


def git_commit_and_push(summary):
    subprocess.run(["git", "config", "--local", "user.name", "Wiki Ingest Bot"], check=True)
    subprocess.run(["git", "config", "--local", "user.email", "bot@wiki.local"], check=True)
    subprocess.run(["git", "add", "wiki/"], check=True)
    
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


# Maps index section headers to wiki subdirectories for auto-generated index pages.
CATEGORY_DIR_MAP = {
    "Skills": "skills",
    "Roles": "roles",
    "Concepts": "concepts",
    "Methodologies": "methodologies",
    "Studies": "studies",
    "Entities": "entities",
    "Synthesis": "synthesis",
}


def sync_subindex_pages(index_md):
    """Parse index_md category tables and write them to category/index.md files.
    Called automatically after every ingest to keep left-nav pages in sync."""
    lines = index_md.split("\n")
    current_cat = None
    current_desc = None
    table_lines = []
    in_table = False
    header_line = None

    for line in lines:
        # Detect ## section headers
        if line.startswith("## ") and not line.startswith("### "):
            # Flush previous category if we were in one
            if current_cat is not None and table_lines:
                _write_subindex(current_cat, current_desc, header_line, table_lines)
            # Start new section
            current_cat = line[3:].strip()
            current_desc = None
            table_lines = []
            in_table = False
            header_line = None
            continue

        if current_cat is None:
            continue

        # Capture description (text between section header and table)
        if current_desc is None and line.strip() and not line.startswith("|") and not line.startswith("##"):
            current_desc = line.strip()

        # Detect table start (pipe followed by dashes, possibly with spaces)
        if line.startswith("|") and "---" in line and "|" in line[1:]:
            in_table = True
            continue

        # Collect table rows
        if in_table:
            if line.startswith("|") and "|" in line[1:]:
                table_lines.append(line)
            else:
                in_table = False

    # Flush last category
    if current_cat is not None and table_lines:
        _write_subindex(current_cat, current_desc, header_line, table_lines)


def _write_subindex(cat_name, description, header_line, table_lines):
    """Write a single sub-index page for the given category."""
    cat_dir = CATEGORY_DIR_MAP.get(cat_name)
    if cat_dir is None:
        return  # not a mapped category (e.g. "Sources")

    path = os.path.join(WIKI_DIR, cat_dir, "index.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    desc = description or ""
    if desc.endswith(":"):
        desc = desc

    # Rebuild table header + body
    table = "| Page | First Observed | Last Updated | Description |\n"
    table += "|------|---------------|-------------|-------------|\n"
    for row in table_lines:
        # Strip leading/trailing pipes and whitespace
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) >= 4:
            table += f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |\n"

    content = f"# {cat_name}\n\n{desc}\n\n{table}\nSee [[index|Home]] for the full catalog.\n"

    old = ""
    if os.path.exists(path):
        with open(path) as fh:
            old = fh.read()

    if old != content:
        with open(path, "w") as fh:
            fh.write(content)
        print(f"  Synced: {path}")


def sync_sources_page():
    """Auto-generate wiki/sources.md from raw/ directory + ingested tracker."""
    ingested = get_ingested_files()
    rows = ""
    if os.path.exists(RAW_DIR):
        for f in sorted(os.listdir(RAW_DIR)):
            if f.endswith(".txt") or f.endswith(".md"):
                # Try to find a log entry date; fall back to tracker presence
                status = "Processed" if f in ingested else "Pending"
                rows += f"| — | {f} | {status} |\n"

    content = "# Sources\n\nSource files processed from `raw/`:\n\n"
    content += "| Date | File | Status |\n|------|------|--------|\n"
    content += rows
    content += "\nSee [[index|Home]] for the full catalog.\n"

    path = os.path.join(WIKI_DIR, "sources.md")
    old = ""
    if os.path.exists(path):
        with open(path) as f:
            old = f.read()

    if old != content:
        with open(path, "w") as f:
            f.write(content)
        print(f"  Synced: {path}")


def sync_figures_page():
    """Auto-generate wiki/figures/index.md from existing figure pages."""
    figures_dir = os.path.join(WIKI_DIR, "figures")
    index_path = os.path.join(figures_dir, "index.md")
    os.makedirs(figures_dir, exist_ok=True)

    # Scan wiki/figures/ for figure pages (not index.md itself)
    figure_pages = []
    for f in sorted(os.listdir(figures_dir)):
        if f.endswith(".md") and f != "index.md":
            slug = f.replace(".md", "")
            # Read the page to extract title and source
            page_path = os.path.join(figures_dir, f)
            with open(page_path) as fh:
                first_line = fh.readline().strip()
            title = first_line.lstrip("# ").strip() if first_line.startswith("#") else slug
            figure_pages.append({"slug": slug, "title": title, "path": f})

    if not figure_pages:
        return

    lines = ["# Figures", "",
             "Catalog of all figures extracted from source documents.",
             "",
             "| Figure | Title |",
             "|--------|-------|"]
    for fp in figure_pages:
        lines.append(f"| [[{fp['slug']}]] | {fp['title']} |")
    lines.append("")
    lines.append("See [[index|Home]] for the full catalog.")

    content = "\n".join(lines) + "\n"
    old = ""
    if os.path.exists(index_path):
        with open(index_path) as f:
            old = f.read()

    if old != content:
        with open(index_path, "w") as f:
            f.write(content)
        print(f"  Synced: {index_path}")


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
    source_name = os.path.basename(filepath)
    sources_block = f"<<<SOURCE: {source_name}\n{source_text}\nSOURCE_END"
    prompt = template.format(
        PROJECT_NAME=PROJECT_NAME,
        DOMAIN=DOMAIN,
        SCHEMA=schema,
        INDEX=index_content,
        SOURCE_COUNT=1,
        SOURCES=sources_block,
    )

    print(f"Calling {MODEL}...")
    response = api_call(
        system_prompt="You are a precise wiki compiler. Output valid JSON exactly as requested. Use [[wikilinks]] for cross-references.",
        user_message=prompt,
        temperature=0.3
    )
    
    print("Applying changes...")
    summary = apply_changes(response)
    mark_as_ingested([source_name])
    
    print(f"Summary: {summary}")

    # Post-pass: detect orphan pages before commit
    orphans = detect_orphans()
    
    git_commit_and_push(summary)
    print("Done!")


if __name__ == "__main__":
    main()
