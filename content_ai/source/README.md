# Source Intelligence (RFC-006 / ES-001 extraction)

Used by APF-001 AI Editorial Workspace and ES-001A Smart News Import.

## Implemented

- Manual URL / pasted-text intake
- **HTTP fetch** of article URLs on workspace **Ingest Source**
- Readable HTML extraction (`<article>`, `<main>`, paragraphs)
- Open Graph / Twitter title + site name
- JSON-LD / Schema.org article metadata (headline, publisher, date, body)
- Publication date, publisher, language, and light country hints
- Placeholder trust score / freshness

## Not yet

- Full credibility ranking / multi-source corroboration
- Paywall bypass or authenticated scrape

Editors can still paste article text manually when fetch/extraction fails.
