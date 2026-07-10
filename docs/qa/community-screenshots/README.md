# Community UI — Product Design QA Screenshots

Captured against local dev server with realistic Persian seed data about life in Sweden.

## Seed data

- **10 discussions** across 8 categories (immigration, work, daily life, law, health, culture, buy/sell, general)
- **5 verified users** (`sara_stockholm`, `ali_goteborg`, `maryam_malmo`, `reza_uppsala`, `neda_linkoping`)
- **Approved replies** on the residency renewal discussion used for detail screenshots

## Viewports

| Prefix | Width |
|--------|-------|
| `desktop-1440` | 1440px |
| `tablet-1024` | 1024px |
| `mobile-390` | 390px |

## Screens

| File suffix | URL / state |
|-------------|-------------|
| `community-home` | `/community/discussions/` |
| `discussion-detail` | Residency renewal discussion with 3 replies |
| `create-discussion` | `/community/discussions/create/` (logged in as `sara_stockholm`) |
| `empty-state` | `/community/search/?q=نتیجه%20خالی%20xyz` |
| `search-results` | `/community/search/?q=اقامت` |

## Note on “Create Discussion Modal”

The MVP implements create as a **dedicated page**, not a modal. Screenshots use the actual `/community/discussions/create/` route.
