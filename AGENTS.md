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
