# Output Schema (v1)

Editorial generation produces labelled sections in two passes.

## Pass 1 — Headline and lead (before body)

```
TITLE:
...
LEAD:
...
```

- `TITLE` must be a fresh Persian headline (do not copy the source-language title).
- `LEAD` is one or two Persian lead paragraphs grounded in the source.
- Do not write the article body in this pass.

## Pass 2 — Body and metadata

```
BODY:
...
SUMMARY:
...
CATEGORY:
...
TAGS:
comma, separated, tags
```

- `TITLE` and `LEAD` are locked from pass 1 and must not be rewritten.
- `BODY` is the full Persian article body.
- `SUMMARY`, `CATEGORY`, and `TAGS` are editorial hints only.
