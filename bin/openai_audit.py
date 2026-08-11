#!/usr/bin/env python3
"""Run a read-only GPT-5.6 Sol audit against a wiki page and source text."""

import argparse
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ingest


API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("AUDIT_MODEL", ingest.AUDIT_MODEL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki-page", required=True, help="Path to the wiki Markdown page")
    parser.add_argument("--source", required=True, help="Path to the supporting raw source")
    parser.add_argument("--output", help="Optional report path; stdout is the default")
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    with open(args.wiki_page, encoding="utf-8") as fh:
        wiki_page = fh.read()
    with open(args.source, encoding="utf-8") as fh:
        source = fh.read()

    prompt = f"""Audit this wiki page against its source. Do not rewrite files.

Return a structured report with:
1. Unsupported or overstated claims
2. Contradictions or missing limitations
3. Broken or misleading cross-references
4. Suggested corrections, with evidence from the source

WIKI PAGE ({args.wiki_page}):
<<<WIKI_START>>>
{wiki_page}
<<<WIKI_END>>>

SOURCE ({args.source}):
<<<SOURCE_START>>>
{source}
<<<SOURCE_END>>>
"""
    response = requests.post(
        f"{API_BASE}/responses",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "instructions": "You are a rigorous evidence auditor. Return only the audit report.",
            "input": prompt,
            "reasoning": {"effort": "medium"},
            "max_output_tokens": 32000,
        },
        timeout=600,
    )
    response.raise_for_status()
    result = response.json()
    report = result.get("output_text")
    if not report:
        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    report = content["text"]
                    break
            if report:
                break
    if not report:
        raise RuntimeError("OpenAI audit response did not contain output text")
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"Audit report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
