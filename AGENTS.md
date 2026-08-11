# ICN Jobs Literature Review — Skills Gap Research Wiki

## Project Overview

Structured knowledge base from literature and job listing data
for the Insights Career Network's skills gap research.

Pipeline:
1. Submit source files (PDFs, reports) to `sources/`
2. Preprocess extracts text + chart images → `raw/` + `wiki/figures/`
3. Ingest sends `raw/` to an LLM, extracts structured knowledge → `wiki/`
4. MkDocs builds the wiki into a public GitHub Pages site

## Architecture

```
sources/     → Raw source files (PDFs, txt, md) submitted by contributors.
raw/         → Immutable extracted text files. Never edit files here.
wiki/        → Agent-compiled knowledge base.
  concepts/  → Cross-cutting ideas, trends, frameworks
  skills/    → Skills, competencies, requirements
  roles/     → Job roles, positions, career paths
  entities/  → Companies, research firms, tools, platforms
  studies/   → Research studies, papers, reports
  methodologies/ → Research methodologies
  figures/   → Figure pages with embedded images
  synthesis/ → Timeline pages, trend reports, gap analysis
  index.md   → Master catalog of all wiki pages
  log.md     → Chronological ingest log
  extra.css  → Table font-size override
```

## File Reference

| File | Purpose |
|------|---------|
| `ingest.py` | Single-file ingest + post-processing (sub-index sync, sources sync, |
| | figures catalog sync, orphan detection, JSON repair, git commit). |
| `bin/ingest_batch.py` | Batch ingest. Processes ALL unprocessed `raw/` files in one LLM call |
| | for cross-source synthesis. Falls back to per-file `ingest.main()`. |
| `bin/preprocess.py` | Extract text (pdfplumber) + chart images (vision model) from PDFs. |
| | Saves chart JPEGs to `wiki/figures/<slug>/fig-N.jpg`. |
| `prompt.txt` | LLM prompt template. Instructs extraction of skills, roles, concepts, |
| | entities, studies, methodologies, **and figures** into structured JSON. |
| `config.json` | Project config: MODEL, PROJECT_NAME, DOMAIN, STRICT_MODE flag. |
| `mkdocs.yml` | MkDocs config (Material theme, roamlinks, nav with Sources + Figures). |
| `requirements-docs.txt` | Python deps: mkdocs, mkdocs-material, mkdocs-roamlinks-plugin. |
| `AGENTS.md` | This file. Agent instructions for the project. |
| `CONTRIBUTING.md` | Instructions for contributors submitting source files via GitHub. |

## Pipeline Details

### Preprocessing (`bin/preprocess.py`)
- Trigger: push to `sources/**` (GitHub Actions)
- **Pass 1**: pdfplumber extracts body text → `raw/<name>.txt`
- **Pass 2**: Renders each PDF page to image, sends to vision model (Gemini 2.5 Flash)
  - Model describes charts/tables: Type, Title, Axes, Key data points, Main finding
  - Saves chart JPEG to `wiki/figures/<slug>/fig-N.jpg`
  - Writes description + image path to `raw/<name>.figures.md`
- Idempotent: skips text extraction if `.txt` exists; re-checks figures

### Ingest (`ingest.py` + `bin/ingest_batch.py`)
- Trigger: daily 23:00 UTC or manual `workflow_dispatch`
- Batch processes ALL unprocessed `raw/` files in one LLM call
- Falls back to single-file mode if batch JSON parse fails
- LLM output (JSON) creates/updates wiki pages, index, log entry
- Post-processing after every ingest:
  - **`sync_subindex_pages()`** — regenerates `skills/index.md`, etc. from index.md tables
  - **`sync_sources_page()`** — regenerates `sources.md` from `raw/` + tracker
  - **`sync_figures_page()`** — regenerates `figures/index.md` catalog from figure pages
  - **`detect_orphans()`** — warns (or aborts in STRICT_MODE) on pages with 0 incoming wikilinks
- Tracks ingested files via `wiki/.ingested.json` (JSON array of filenames)
- Applies `repair_json()` on JSON parse failure (fixes trailing commas, missing commas between objects)

### Figure Handling
- `preprocess.py` saves chart images as JPEGs to `wiki/figures/<slug>/`
- Image path in `.figures.md`: `<slug>/fig-N.jpg` (relative to `wiki/`)
- Prompt tells LLM to create one wiki page per figure at `wiki/figures/<source-slug>-fig-N-title.md`
  with embedded image, source cross-link, and backlinks from relevant content pages
- `wiki/figures/index.md` auto-generated catalog with wikilinks to all figure pages

### Deploy (`.github/workflows/deploy.yml`)
- Trigger: push to `wiki/**`, `mkdocs.yml`, or `requirements-docs.txt`
- Uses `mkdocs gh-deploy --force` to push built site to `gh-pages` branch
- Converts `[[wikilinks]]` to clickable links via roamlinks plugin

## Ingest Workflow

When new files appear in `raw/`:

1. **Read** the new file(s) completely.
2. **Extract**:
   - Companies, research firms, tools, platforms → `wiki/entities/`
   - Trends, skills frameworks, themes → `wiki/concepts/`
   - Skills, competencies, requirements → `wiki/skills/`
   - Job roles, career paths → `wiki/roles/`
   - Methodologies → `wiki/methodologies/`
   - Key findings from papers → `wiki/studies/`
   - Figures and charts → `wiki/figures/<slug>-fig-N-title.md`
3. **Create or update** wiki pages. Append dated "Update" section, never rewrite.
   Link between pages using `[[wikilinks]]`. Cross-reference figures from content pages.
4. **Update `wiki/index.md`** — add new pages to catalog tables.
5. **Update `wiki/log.md`** — append: `YYYY-MM-DD: Ingested [file]. Created N, updated M.`

## Page Conventions

- **Entity pages**: Name, what they do, relevance to AI/MRX, backlinks
- **Concept pages**: Definition, first observed, examples, related entities/concepts
- **Synthesis pages**: Broader analysis, timelines, comparisons, gap analysis
- **Figure pages**: Embedded image, full vision-model description, source wikilink, page number
- **Wikilinks**: `[[page-name]]` format. Keep lowercase with hyphens.

## Rules

- `raw/` is immutable. Never edit or delete files there.
- Every ingest must be logged in `wiki/log.md`.
- Prefer updating existing pages over creating near-duplicates.
- When in doubt about a connection, add it with a `?` note rather than omitting it.
- Orphans (pages with 0 incoming wikilinks) cause abort when `STRICT_MODE=true`.

## Lint Workflow (run periodically)

1. Check for broken `[[wikilinks]]` (roamlinks warnings during build).
2. Check for stale pages not updated in 90+ days.
3. Check for orphan pages (no incoming links) via `detect_orphans()`.
4. Verify `wiki/index.md` matches actual wiki contents.

## Planned Build: Model Routing and Wiki Rebuild

This section records the agreed implementation plan for branch
`codex/model-routing-rebuild`. Continue from this plan if work is handed to
another tool or agent.

### Model roles

- **Vision extraction:** Gemini via OpenRouter. Default target:
  `google/gemini-3.6-flash`.
- **Routine synthesis:** Qwen via OpenRouter. Default target:
  `qwen/qwen3-235b-a22b-2507` (Instruct; use the Thinking variant only when
  explicitly requested for difficult analysis).
- **Large rebuilds:** GPT-5.6 Luna through the direct OpenAI API and Batch API:
  `gpt-5.6-luna`.
- **High-stakes audit:** GPT-5.6 Sol through the direct OpenAI API only when
  explicitly requested or when a difficult synthesis requires escalation:
  `gpt-5.6-sol`.

Never commit API keys. GitHub Actions secrets are `OPENROUTER_API_KEY` and
`OPENAI_API_KEY`; model names may be configured as non-secret variables.

### Implementation sequence

1. Add explicit model-role configuration without breaking the existing
   OpenRouter defaults.
2. Keep `bin/preprocess.py` on the OpenRouter vision endpoint and make its
   model selection explicit and reproducible.
3. Keep routine `ingest.py` and `bin/ingest_batch.py` on OpenRouter/Qwen.
4. Add a separate direct OpenAI Batch rebuild path. It must upload JSONL batch
   requests, submit a batch, poll for completion, parse each result, and apply
   changes only after the full batch response is validated.
5. Add an explicit Sol audit path. It must never run automatically during
   routine ingest.
6. Before rebuilding, preserve the existing `wiki/` on the branch or in an
   archive directory. Do not delete `sources/` or `raw/`; `raw/` is immutable.
7. Rebuild canonical wiki pages from the source manifest rather than
   repeatedly appending updates from the same raw file. Repair and regenerate
   `wiki/.ingested.json`, `wiki/index.md`, category indexes, `wiki/sources.md`,
   `wiki/figures/index.md`, and `wiki/log.md` as part of the rebuild.
8. Remove duplicate or stale figure pages only after their source/image
   mapping has been checked and the archived wiki remains recoverable.

### Image requirements

- Store extracted images at `wiki/figures/<source-slug>/fig-N.jpg`.
- On a figure page located directly in `wiki/figures/`, reference the image as
  `<source-slug>/fig-N.jpg`.
- Do not generate a figure page unless its referenced image exists.
- Every figure page must include the actual Markdown image, source study link,
  source page number, and vision-model description.
- Add validation that resolves every image reference against the source tree.

### Required validation before merge

- No uncommitted secrets or credentials.
- Every `[[wikilink]]` resolves to a page or an intentionally documented
  external/ unresolved reference.
- Every Markdown image target resolves to a committed file.
- No duplicate figure identity exists for the same source and figure number.
- No unexpected orphan pages when `STRICT_MODE=true`.
- `mkdocs build --strict` succeeds.
- A representative study page and figure page are visually checked in the
  rendered site.
- Run a dry-run rebuild or fixture test before submitting a real OpenAI Batch
  request, because Batch requests incur costs and are asynchronous.

### Handoff state

The work branch is `codex/model-routing-rebuild`. The current `main` branch is
the last synchronized GitHub state. The OpenAI key has been added to GitHub
Actions as `OPENAI_API_KEY`; do not request or print its value.
