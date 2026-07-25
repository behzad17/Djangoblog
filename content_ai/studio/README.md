# AI Studio (APF-002)

Admin/editor control centre for experimenting with Peyvand AI.

- Docs: [`docs/ai/features/APF-002.md`](../../docs/ai/features/APF-002.md)
- Flag: `ENABLE_AI_STUDIO`
- Never modifies production prompts/knowledge
- Never publishes content

## Package layout

| Module | Role |
|--------|------|
| `modules.py` | Lab catalogue |
| `session.py` | Session + generation history DTOs |
| `store.py` | Django session persistence |
| `services.py` | `StudioService` composition layer |
| `views.py` | Page + JSON API |
