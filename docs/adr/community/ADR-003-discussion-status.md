# ADR-003: Discussion status — Open / Closed / Hidden

## Status

Accepted (MVP); moderation state extension **Proposed**

## Context

Community discussions need lifecycle states for public visibility and admin workflow. Replies already have a dedicated `approved` flag for moderation. Discussions publish immediately on create in MVP and do not yet have an equivalent moderation field.

The Pending Items Dashboard (PR-010) needs a count and admin link for discussions awaiting review.

## Decision

### MVP (implemented)

Use `DiscussionStatus` TextChoices:

| Value | Meaning |
|-------|---------|
| `open` | Public, accepts replies |
| `closed` | Public, read-only |
| `hidden` | Not shown on public selectors |

**Temporary moderation queue:** Until a dedicated moderation state exists, `list_pending_discussions()` and the admin dashboard treat **non-deleted discussions with `status=hidden`** as pending moderation. The Review button filters the Discussion admin changelist with `?status__exact=hidden`.

This is a pragmatic MVP shortcut: visibility (`hidden`) is overloaded with “awaiting moderation.”

### Future release (proposed)

Introduce a separate **moderation state** (e.g. `PENDING`) distinct from visibility:

- **Moderation** — whether staff has approved the discussion (e.g. `pending`, `approved`, `rejected`)
- **Visibility** — whether the discussion is publicly visible (`open`, `closed`, `hidden`)

When implemented:

1. Add moderation field(s) or a `pending` status that is not conflated with `hidden`
2. Update `list_pending_discussions()` to query the moderation queue, not `status=hidden`
3. Update the Pending Items Dashboard filter URL accordingly
4. Migrate any MVP data where `hidden` was used only as a moderation queue

## Consequences

### Positive

- MVP dashboard integration without a schema change
- Clear path documented for separating moderation from visibility

### Negative

- `hidden` currently mixes “moderation queue” and “admin-hidden from public” semantics
- Dashboard count may stay at 0 until discussions are explicitly set to `hidden`

## Alternatives considered

- **Add `approved` on Discussion in MVP** — rejected for PR-010 scope; replies already use this pattern
- **Use soft-deleted discussions as pending** — rejected; deletion is a different admin action than moderation
- **Skip discussions card until PENDING exists** — rejected; PR-010 requires the card with a workable filter
