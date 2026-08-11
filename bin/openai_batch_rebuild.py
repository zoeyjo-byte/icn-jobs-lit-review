#!/usr/bin/env python3
"""Submit and apply a manual OpenAI Batch API wiki rebuild.

This path is intentionally separate from routine OpenRouter ingest. It does
not run from the scheduled ingest workflow and never commits or pushes by
itself. Use --dry-run first, then --submit --wait --apply after reviewing the
planned source set.
"""

import argparse
import io
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ingest


OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("REBUILD_MODEL", ingest.REBUILD_MODEL)
MAX_CHARS_PER_FILE = int(os.environ.get("MAX_CHARS_PER_FILE", "50000"))
MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "128000"))


def headers():
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return {"Authorization": f"Bearer {OPENAI_API_KEY}"}


def all_source_files():
    files = []
    if os.path.isdir(ingest.RAW_DIR):
        for name in sorted(os.listdir(ingest.RAW_DIR)):
            if name.endswith((".txt", ".md")):
                files.append(os.path.join(ingest.RAW_DIR, name))
    return files


def sources_block(filepaths):
    blocks = []
    for filepath in filepaths:
        with open(filepath, encoding="utf-8") as fh:
            content = fh.read()
        if len(content) > MAX_CHARS_PER_FILE:
            content = content[:MAX_CHARS_PER_FILE]
            print(f"Truncated {filepath} to {MAX_CHARS_PER_FILE} characters")
        name = os.path.basename(filepath)
        blocks.append(f"<<<SOURCE: {name}\n{content}\nSOURCE_END")
    return "\n\n".join(blocks)


def build_prompt(filepaths):
    template = ingest.read_prompt_template()
    rebuild_note = """
REBUILD MODE:
This is a controlled rebuild from the complete raw source set. Produce one
canonical page per study, concept, role, entity, methodology, and figure.
Merge duplicate topics instead of appending repeated update sections. Use only
claims supported by the supplied sources. For figures, create a page only when
the referenced image exists under wiki/figures/<source-slug>/fig-N.jpg, and use
the page-relative image path <source-slug>/fig-N.jpg.
""".strip()
    return template.format(
        PROJECT_NAME=ingest.PROJECT_NAME,
        DOMAIN=ingest.DOMAIN,
        SCHEMA=ingest.read_schema(),
        INDEX=ingest.read_index(),
        SOURCE_COUNT=len(filepaths),
        SOURCES=sources_block(filepaths),
    ) + "\n\n" + rebuild_note


def batch_request(prompt):
    body = {
        "model": MODEL,
        "instructions": (
            "You are the canonical wiki rebuild compiler. Return only valid "
            "JSON in the requested schema. Reconcile sources carefully and "
            "never invent image files."
        ),
        "input": prompt,
        "reasoning": {"effort": "medium"},
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    line = {
        "custom_id": "wiki-rebuild",
        "method": "POST",
        "url": "/v1/responses",
        "body": body,
    }
    return (json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8")


def submit(prompt):
    payload = batch_request(prompt)
    upload = requests.post(
        f"{OPENAI_API_BASE}/files",
        headers=headers(),
        files={"file": ("wiki-rebuild.jsonl", io.BytesIO(payload), "application/jsonl")},
        data={"purpose": "batch"},
        timeout=120,
    )
    upload.raise_for_status()
    file_id = upload.json()["id"]
    batch = requests.post(
        f"{OPENAI_API_BASE}/batches",
        headers={**headers(), "Content-Type": "application/json"},
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/responses",
            "completion_window": "24h",
            "metadata": {"project": ingest.PROJECT_NAME, "purpose": "wiki-rebuild"},
        },
        timeout=120,
    )
    batch.raise_for_status()
    result = batch.json()
    print(f"Submitted OpenAI Batch: {result['id']} (model={MODEL})")
    return result["id"]


def wait_for_batch(batch_id, poll_seconds):
    while True:
        response = requests.get(
            f"{OPENAI_API_BASE}/batches/{batch_id}", headers=headers(), timeout=120
        )
        response.raise_for_status()
        result = response.json()
        status = result.get("status")
        print(f"Batch {batch_id}: {status}")
        if status in {"completed", "failed", "expired", "cancelled"}:
            return result
        time.sleep(poll_seconds)


def extract_result(batch):
    output_file_id = batch.get("output_file_id")
    if not output_file_id:
        error_file_id = batch.get("error_file_id")
        detail = ""
        if error_file_id:
            error_response = requests.get(
                f"{OPENAI_API_BASE}/files/{error_file_id}/content",
                headers=headers(),
                timeout=120,
            )
            error_response.raise_for_status()
            detail = f" Error file: {error_response.text[:4000]}"
        raise RuntimeError(f"Batch completed without output_file_id: {batch}.{detail}")
    response = requests.get(
        f"{OPENAI_API_BASE}/files/{output_file_id}/content",
        headers=headers(),
        timeout=300,
    )
    response.raise_for_status()
    records = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    if len(records) != 1 or records[0].get("custom_id") != "wiki-rebuild":
        raise RuntimeError("Unexpected Batch output record set")
    record = records[0]
    if record.get("error"):
        raise RuntimeError(f"Batch request failed: {record['error']}")
    body = record.get("response", {}).get("body", {})
    if body.get("output_text"):
        return body["output_text"]
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise RuntimeError("Batch response did not contain model content")


def validate_json(response_text):
    candidate = response_text.strip()
    if "```json" in candidate:
        candidate = candidate.split("```json", 1)[1].split("```", 1)[0]
    start, end = candidate.find("{"), candidate.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model response contains no JSON object")
    candidate = candidate[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return json.loads(ingest.repair_json(candidate))


def apply_validated(response_text):
    changes = validate_json(response_text)
    required = {"files_to_create", "files_to_update", "index_md", "log_entry", "summary"}
    missing = required - set(changes)
    if missing:
        raise ValueError(f"Batch JSON missing required fields: {sorted(missing)}")
    ingest.apply_changes(json.dumps(changes, ensure_ascii=False))
    orphans = ingest.detect_orphans()
    if orphans and ingest.STRICT_MODE:
        raise RuntimeError(f"Strict rebuild produced orphan pages: {orphans}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="build and validate request without API submission")
    parser.add_argument("--submit", action="store_true", help="submit a new Batch request")
    parser.add_argument("--batch-id", help="poll an existing Batch request")
    parser.add_argument("--wait", action="store_true", help="poll until the Batch completes")
    parser.add_argument("--apply", action="store_true", help="apply validated output to wiki/")
    parser.add_argument("--poll-seconds", type=int, default=30)
    args = parser.parse_args()

    files = all_source_files()
    if not files:
        raise RuntimeError("No raw source files found")
    prompt = build_prompt(files)
    print(f"Sources: {len(files)}; prompt: {len(prompt)} characters; model: {MODEL}")
    if args.dry_run:
        batch_request(prompt)
        print("Dry run passed; no API request submitted.")
        return
    if args.submit and args.batch_id:
        parser.error("Use --submit or --batch-id, not both")
    batch_id = args.batch_id or (submit(prompt) if args.submit else None)
    if not batch_id:
        parser.error("Specify --dry-run, --submit, or --batch-id")
    if not args.wait:
        print(f"Resume with: --batch-id {batch_id} --wait --apply")
        return
    result = wait_for_batch(batch_id, args.poll_seconds)
    if result.get("status") != "completed":
        raise RuntimeError(f"Batch ended with status {result.get('status')}")
    if not args.apply:
        response_text = extract_result(result)
        validate_json(response_text)
        print("Batch completed and output JSON validated; rerun with --apply to write wiki/")
        return
    response_text = extract_result(result)
    apply_validated(response_text)
    print("Applied validated Batch output to wiki/. Review and commit explicitly.")


if __name__ == "__main__":
    main()
