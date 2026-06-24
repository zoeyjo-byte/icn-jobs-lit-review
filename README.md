# ICN Jobs Literature Review — Skills Gap Research Wiki

A structured knowledge base for analyzing skills gaps in the market research industry, built from literature review and job listing data.

## Structure

```
raw/                    # Immutable source documents (job listings, research papers, reports)
wiki/                   # Agent-compiled knowledge base
├── concepts/          # Market research trends, frameworks, recurring themes
├── skills/            # Skills, competencies, requirements from job listings
├── roles/             # Market research job roles, positions, career paths
├── entities/          # Companies, research firms, tools, platforms mentioned
├── studies/           # Research studies, papers, reports on skills gaps
├── methodologies/     # Research methodologies used in literature
└── synthesis/         # Timeline pages, trend reports, comparison pages, gap analysis
index.md               # Master catalog of all wiki pages and their relationships
log.md                 # Chronological ingest log
AGENTS.md              # Wiki schema and workflow instructions
```

## Ingest Workflow

When new files are added to `raw/`:

1. The agent reads the source file (job listing, research paper, industry report)
2. Extracts:
   - Market research trends and frameworks → `wiki/concepts/`
   - Skills and competencies from job listings → `wiki/skills/`
   - Job roles and career paths → `wiki/roles/`
   - Companies and research firms → `wiki/entities/`
   - Research studies → `wiki/studies/`
   - Methodologies → `wiki/methodologies/`
3. Creates or updates wiki pages with `[[wikilinks]]` cross-references
4. Updates `index.md` catalog and `log.md` audit trail

## Setup for Automated Ingest

1. **Set environment variables**:
   ```bash
   export OPENROUTER_API_KEY="your-api-key"
   export PROJECT_NAME="ICN Jobs Literature Review"
   export DOMAIN="Market Research Skills Gap"
   ```

2. **Add raw files** to the `raw/` directory as `.txt` files

3. **Run ingest manually**:
   ```bash
   python ingest.py
   ```

4. **GitHub Actions** will run daily at 10:00 UTC if configured

## Secrets Required

For GitHub Actions to work, add these repository secrets:
- `OPENROUTER_API_KEY` - API key for OpenRouter LLM access

For local development, set these environment variables.

## Project Focus

This wiki supports research for the Insights Career Network (ICN) to identify:
- Skills listed in market research job postings vs. skills actually sought by hiring managers
- Emerging competencies in AI/ML for market research
- Gaps between academic training and industry needs
- Career progression patterns in market research roles