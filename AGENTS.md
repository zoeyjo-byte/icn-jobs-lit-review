# ICN Jobs Literature Review — Skills Gap Research Wiki

## Project Overview

This repo builds a structured knowledge base from literature and job listing data
for the Insights Career Network's skills gap research project. The pipeline:

1. Researchers submit source files (PDFs, reports) to `sources/`
2. Automated preprocessing extracts text and charts → `raw/`
3. Automated ingest feeds `raw/` to an LLM, which extracts structured knowledge → `wiki/`
4. MkDocs builds the wiki into a public GitHub Pages site

## Architecture

```
sources/     → Raw source files (PDFs, txt, md) submitted by contributors.
raw/         → Immutable extracted text files. Never edit files here.
wiki/        → Agent-compiled knowledge base. The agent writes and maintains this.
  concepts/  → Cross-cutting ideas, trends, frameworks in market research
  skills/    → Skills, competencies, requirements found in job listings
  roles/     → Market research job roles, positions, career paths
  entities/  → Companies, research firms, tools, platforms mentioned
  studies/   → Research studies, papers, reports on skills gaps
  methodologies/ → Research methodologies used in literature
  synthesis/ → Timeline pages, trend reports, comparison pages, gap analysis
  index.md   → Master catalog of all wiki pages and their relationships
  log.md     → Chronological ingest log
```

## File Reference

| File | Purpose |
|------|---------|
| `ingest.py` | Single-file ingest. Reads one unprocessed file from `raw/`, sends to |
| | OpenRouter via `prompt.txt` template, applies JSON response to `wiki/`. |
| `bin/ingest_batch.py` | Batch ingest. Processes ALL unprocessed `raw/` files in one LLM call |
| | for cross-source synthesis. Falls back to per-file `ingest.main()` on error. |
| `bin/preprocess.py` | Extracts text and chart images from PDFs in `sources/` → `raw/`. |
| | Uses pdfplumber for text, vision model for chart descriptions. |
| `prompt.txt` | LLM prompt template. Instructs the model to extract skills, roles, |
| | concepts, entities, studies, methodologies as structured JSON. |
| `config.json` | Project config: MODEL, PROJECT_NAME, DOMAIN, STRICT_MODE flag. |
| `mkdocs.yml` | MkDocs config for the public GitHub Pages site. Uses Material theme, |
| | roamlinks plugin (converts `[[wikilinks]]` to clickable links). |
| `requirements-docs.txt` | Python deps: mkdocs, mkdocs-material, mkdocs-roamlinks-plugin. |
| `AGENTS.md` | This file. Agent instructions for the project. |
| `CONTRIBUTING.md` | Instructions for contributors submitting source files via GitHub. |

## GitHub Actions Workflows

Three workflows chain together to form the automated pipeline:

```
sources/ push ──→ Preprocess ──→ raw/ commit ──→ Ingest ──→ wiki/ commit ──→ Deploy
   (triggers)       (extract      (triggers       (LLM       (triggers       (builds
                    text/figures)  ingest.yml)    extracts)   deploy.yml)    site)
```

### 1. Preprocess (`.github/workflows/preprocess.yml`)
- Trigger: push to `sources/**`
- Steps: install pdfplumber+Pillow, run `python3 bin/preprocess.py`
- Output: extracted `.txt` and `.figures.md` files in `raw/`
- Runs on `python3`, uses `OPENROUTER_API_KEY` and `VISION_MODEL` secrets

### 2. Ingest (`.github/workflows/ingest.yml`)
- Trigger: daily at 23:00 UTC, or manual `workflow_dispatch`
- Steps: install requests, run `python3 bin/ingest_batch.py`
- Batch processes ALL unprocessed `raw/` files in one LLM call
- Falls back to single-file mode (`ingest.py`) if batch fails
- Commits wiki changes to main

### 3. Deploy (`.github/workflows/deploy.yml`)
- Trigger: push to `wiki/**`, `mkdocs.yml`, or `requirements-docs.txt`
- Steps: install mkdocs stack, run `mkdocs build`, deploy to GitHub Pages
- Converts `[[wikilinks]]` to clickable links via roamlinks plugin

## Ingest Workflow

When new files appear in `raw/`:

1. **Read** the new file(s) completely.
2. **Extract**:
   - Companies, research firms, tools, platforms mentioned (→ `wiki/entities/`)
   - Market research trends, skills frameworks, recurring themes (→ `wiki/concepts/`)
   - Skills, competencies, requirements found in job listings (→ `wiki/skills/`)
   - Job roles, positions, career paths in market research (→ `wiki/roles/`)
   - Research methodologies used in studies (→ `wiki/methodologies/`)
   - Key findings from research papers and reports (→ `wiki/studies/`)
3. **Create or update** wiki pages. If a page exists, append a dated "Update" section rather than rewriting. Link between related pages using `[[wikilinks]]`.
4. **Update `wiki/index.md`** — add any new pages to the catalog under the appropriate section.
5. **Update `wiki/log.md`** — append a line: `YYYY-MM-DD: Ingested [filename]. Created X new pages, updated Y existing pages.`

## Query Workflow

When asked a question:

1. Start at `wiki/index.md` to understand what pages exist.
2. Follow `[[wikilinks]]` to relevant pages.
3. Synthesize an answer from the wiki content.
4. If the wiki lacks sufficient information, acknowledge the gap — do not fabricate.

## Page Conventions

- **Entity pages**: Name, what they do, why relevant to AI/MRX, key appearances in the newsletter, backlinks to related concepts.
- **Concept pages**: Definition, first observed (date), key examples from the newsletter, related entities, related concepts, evolving over time.
- **Synthesis pages**: Broader analysis pulling from multiple entities and concepts. Timeline pages, trend comparisons, "state of X" overviews.
- **Wikilinks**: Use `[[page-name]]` format for all cross-references. Keep page names lowercase with hyphens.

## Lint Workflow (run periodically)

1. Check for broken `[[wikilinks]]`.
2. Check for stale pages not updated in 90+ days — flag in `wiki/index.md`.
3. Check for orphan pages (no incoming links) — add connections or flag.
4. Verify `wiki/index.md` matches actual wiki contents.

## Rules

- `raw/` is immutable. Never edit or delete files there.
- Every ingest must be logged in `wiki/log.md`.
- Prefer updating existing pages over creating near-duplicates.
- When in doubt about a connection, add it with a `?` note rather than omitting it.
