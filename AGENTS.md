# LLM Wiki Schema — AI + MRX Newsletter Knowledge Base

## Architecture

This vault follows Karpathy's LLM Wiki pattern: raw/         → Immutable source documents. Never edit files here.
wiki/        → Agent-compiled knowledge base. The agent writes and maintains this.
concepts/  → Cross-cutting ideas, trends, frameworks
entities/  → Companies, products, people, newsletters tracked
synthesis/ → Timeline pages, trend reports, comparison pages
index.md     → Master catalog of all wiki pages and their relationships
log.md       → Chronological ingest log ## Source Format

Files in `raw/` are daily text digests named `YYYY-MM-DD-newsletter-digest.txt`.
Each digest contains summaries of AI industry news and market research news from multiple newsletters, compiled into a single day's file.

## Ingest Workflow

When new files appear in `raw/`:

1. **Read** the new file(s) completely.
2. **Extract**:
   - Companies, products, and people mentioned (→ `wiki/entities/`)
   - AI trends, MRX developments, frameworks, recurring themes (→ `wiki/concepts/`)
   - Notable launches, funding rounds, partnerships, policy changes
3. **Create or update** wiki pages. If a page exists, append a dated "Update" section rather than rewriting. Link between related pages using `[[wikilinks]]`.
4. **Update `index.md`** — add any new pages to the catalog under the appropriate section.
5. **Update `log.md`** — append a line: `YYYY-MM-DD: Ingested [filename]. Created X new pages, updated Y existing pages.`

## Query Workflow

When asked a question:

1. Start at `index.md` to understand what pages exist.
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
2. Check for stale pages not updated in 90+ days — flag in `index.md`.
3. Check for orphan pages (no incoming links) — add connections or flag.
4. Verify `index.md` matches actual wiki contents.

## Rules

- `raw/` is immutable. Never edit or delete files there.
- Every ingest must be logged in `log.md`.
- Prefer updating existing pages over creating near-duplicates.
- When in doubt about a connection, add it with a `?` note rather than omitting it.