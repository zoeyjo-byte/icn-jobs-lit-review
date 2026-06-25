# Contributing Sources

Thank you for contributing source materials to the ICN Jobs Literature Review.
This wiki is built from research sources (PDFs, reports, job listings, papers)
submitted by trusted contributors and compiled by an automated ingest agent.

## How to submit a source file

You don't need to install any software or know git. You can do everything
from the GitHub web interface in three steps.

### Step 1: Open the sources folder

Go to:
https://github.com/zoeyjo-byte/icn-jobs-lit-review/tree/main/sources

### Step 2: Upload your file

1. Click **"Add file"** → **"Upload files"**
2. Drag your PDF (or .txt, .md) into the box
3. In the commit message, write a short description, e.g.:
   `Add PwC 2026 Global AI Jobs Barometer report`
4. **Important:** select **"Create a new branch"** (not "Commit directly to main")
5. Click **"Propose changes"**

### Step 3: Open a pull request

1. Click **"Create pull request"**
2. (Optional) Add a note about what the source covers
3. Click **"Create pull request"** again

A maintainer will review your submission. Once approved and merged, the
ingest pipeline runs automatically within the hour and extracts findings
into the wiki.

## What happens after you submit

1. **Merge:** maintainer reviews the PR and merges it
2. **Preprocess:** the pipeline extracts text and chart data from your
   PDF into `raw/` (text-only files the wiki builder can read)
3. **Ingest:** the agent analyzes the extracted text and figures, then
   creates or updates wiki pages under `wiki/`

You can watch the progress under the **Actions** tab of the repository.

## Rules

- Only upload materials you have the right to share (your own research,
  publicly available reports, licensed content, etc.)
- Place files in `sources/` — never in `raw/` (that folder is generated
  automatically)
- One source per PR is preferred (easier to review), but multiple related
  files in one PR are fine
- Accepted file types: `.pdf`, `.txt`, `.md`

## Questions

If you're unsure whether a source is relevant, open a pull request anyway
and add a note. Maintainers will help decide where it fits.