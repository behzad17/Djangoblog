# Community Engineering Principles

These principles govern the design and implementation of the Peyvand Community module.

## Architecture

- **Business logic belongs in Services.** Views, signals, and admin actions delegate to service functions. Services own transactions and side effects.
- **Views remain thin.** Views authenticate, authorize, call selectors or services, and render responses. No ORM queries or business rules in views.
- **Selectors never modify data.** The selectors package is read-only. All writes go through services.
- **Models describe data, not workflows.** Model methods are limited to display helpers and simple computed properties. No cross-model orchestration on models.
- **Signals never contain business logic.** Signals may connect events to dispatchers but must call services or notification helpers, not implement rules inline.

## Data integrity

- **Slugs are immutable after publication.** Once a discussion is publicly visible, its slug must not change.
- **Every business rule must be configurable.** Thresholds, rate limits, and search parameters live in Django settings, not hardcoded constants.

## Quality and documentation

- **Every feature requires tests.** Service tests first, then view tests. No feature is complete without coverage of happy path and permission boundaries.
- **Every public architectural change must be documented by ADR.** When a decision affects module boundaries, data models, or integration contracts, update or add an ADR in `docs/adr/community/` before merging.

## Module size

- Prefer packages over large files. No single module should grow beyond approximately 200 lines. Split by responsibility when approaching that limit.
