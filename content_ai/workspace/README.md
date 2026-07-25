# AI Editorial Workspace (APF-001)

Staff-facing editorial workspace that **composes** existing AI packages.

- Docs: [`docs/ai/features/APF-001.md`](../../docs/ai/features/APF-001.md)
- Flag: `ENABLE_AI_EDITORIAL_WORKSPACE`
- Never auto-publishes; does not replace Blog Admin post creation

## Package layout

| Module | Role |
|--------|------|
| `session.py` | Sections, history, session DTO |
| `actions.py` | Assistant action catalogue |
| `services.py` | `WorkspaceService` composition layer |
| `store.py` | Django session persistence |
| `views.py` | Page + JSON API |

## Safety

Publishing remains human-only via Blog Admin.
