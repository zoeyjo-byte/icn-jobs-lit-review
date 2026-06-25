#!/usr/bin/env python3
"""
LLM Wiki Batch Ingest — processes ALL unprocessed raw/ files in one LLM call
for cross-source synthesis and cost efficiency (one prompt overhead).

Falls back to per-file mode (single-file ingest.py) if the batch call fails,
so a single bad source doesn't block the whole queue.
"""

import os
import sys
import json
import requests
import subprocess

# Reuse helpers from ingest.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ingest


def get_unprocessed_files():
    """Return all raw/*.txt and *.md files not yet in the log."""
    ingested = ingest.get_ingested_files()
    files = []
    if os.path.exists(ingest.RAW_DIR):
        for f in sorted(os.listdir(ingest.RAW_DIR)):
            if (f.endswith(".txt") or f.endswith(".md")) and f not in ingested:
                files.append(os.path.join(ingest.RAW_DIR, f))
    return files


def build_sources_block(filepaths, max_chars_per_file=50000):
    """Concatenate all source files with per-source delimiters.

    Format matches what prompt.txt expects:
      <<<SOURCE: filename.txt
      ...content...
      SOURCE_END
      <<<SOURCE: next.txt
      ...
    """
    blocks = []
    for fp in filepaths:
        with open(fp) as f:
            text = f.read()
        if len(text) > max_chars_per_file:
            text = text[:max_chars_per_file]
            print(f"  Truncated {fp} to {max_chars_per_file} chars")
        name = os.path.basename(fp)
        blocks.append(f"<<<SOURCE: {name}\n{text}\nSOURCE_END")
    return "\n\n".join(blocks)


def batch_api_call(prompt):
    """Single LLM call with all sources. Returns response text or raises."""
    headers = {
        "Authorization": f"Bearer {ingest.API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ingest.MODEL,
        "messages": [
            {"role": "system", "content":
                "You are a precise wiki compiler. Output valid JSON exactly "
                "as requested. Use [[wikilinks]] for cross-references. You are "
                "processing multiple source files in one batch — synthesize "
                "across sources and create cross-references between findings."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 32000,
    }
    print(f"Calling {ingest.MODEL} (batch, {len(prompt)} char prompt)...")
    response = requests.post(
        ingest.API_URL, headers=headers, json=payload, timeout=600)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def run_batch(filepaths):
    """Process all files in one LLM call. Returns summary or raises."""
    schema = ingest.read_schema()
    index_content = ingest.read_index()
    sources_block = build_sources_block(filepaths)

    template = ingest.read_prompt_template()
    prompt = template.format(
        PROJECT_NAME=ingest.PROJECT_NAME,
        DOMAIN=ingest.DOMAIN,
        SCHEMA=schema,
        INDEX=index_content,
        SOURCE_COUNT=len(filepaths),
        SOURCES=sources_block,
    )

    response = batch_api_call(prompt)
    summary = ingest.apply_changes(response)
    # Mark all batch files as ingested
    filenames = [os.path.basename(fp) for fp in filepaths]
    ingest.mark_as_ingested(filenames)
    return summary


def run_single_file_fallback(filepath):
    """Fall back to single-file ingest.py for one file."""
    print(f"\nFALLBACK: running single-file ingest for {filepath}")
    # Call the single-file ingest main logic directly
    import importlib
    importlib.reload(ingest)
    ingest.main()


def git_commit_and_push(summary):
    subprocess.run(["git", "config", "--local", "user.name",
                    "Wiki Ingest Bot"], check=True)
    subprocess.run(["git", "config", "--local", "user.email",
                    "bot@wiki.local"], check=True)
    subprocess.run(["git", "add", "wiki/"], check=True)

    result = subprocess.run(["git", "diff", "--staged", "--quiet"],
                            capture_output=True)
    if result.returncode == 0:
        print("No changes to commit.")
        return

    subprocess.run(["git", "commit", "-m", f"Batch ingest: {summary}"],
                  check=True)
    subprocess.run(["git", "push"], check=True)
    print("Committed and pushed.")


def main():
    print("=== LLM Wiki Batch Ingest ===")

    files = get_unprocessed_files()
    if not files:
        print("No new files to ingest. Done.")
        return

    print(f"Found {len(files)} unprocessed file(s):")
    for f in files:
        print(f"  - {f}")

    if not ingest.API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set. Aborting.")
        return

    fallback = os.environ.get("FALLBACK_TO_SINGLE", "1") == "1"

    # Try batch mode first
    try:
        summary = run_batch(files)
        print(f"\nBatch summary: {summary}")

        orphans = ingest.detect_orphans()
        git_commit_and_push(summary)
        print("Batch ingest complete!")
        return

    except Exception as e:
        print(f"\n⚠ BATCH FAILED: {e}")
        if not fallback:
            print("FALLBACK_TO_SINGLE not set. Aborting.")
            raise
        print("Falling back to per-file mode...")

    # Fallback: process each file individually via single-file ingest.py
    # We do this by temporarily running ingest.main() once per file.
    # ingest.py processes one file per run, so we loop.
    for fp in files:
        # Re-check if this file is still unprocessed (a prior fallback
        # run may have processed it)
        still_unprocessed = get_unprocessed_files()
        if fp not in still_unprocessed:
            print(f"  {fp} already processed, skipping.")
            continue

        print(f"\n--- Fallback ingest: {fp} ---")
        try:
            # Run single-file ingest in-process by calling its main
            # with a fresh import (it reads the next unprocessed file)
            ingest.main()
        except Exception as e:
            print(f"  ⚠ Single-file ingest failed for {fp}: {e}")
            continue

    print("Fallback ingest complete.")


if __name__ == "__main__":
    main()