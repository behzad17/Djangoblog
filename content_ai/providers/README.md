# Peyvand AI Provider Platform (RFC-005)

Provider-independent layer for communicating with AI vendors.

**Production OpenAI and Mock providers are unchanged in behaviour.**  
`get_provider()` / `OpenAIProvider` / `MockProvider` remain the live path.

Feature flag: `ENABLE_PROVIDER_PLATFORM = False` (platform manager/factory are
opt-in for future wiring).

---

## Architecture

```
Application / Workflow / Evaluation
            ↓
      ProviderManager  (optional)
            ↓
      ProviderFactory
            ↓
      ProviderRegistry
            ↓
      BaseAIProvider adapters
            ↓
      Vendor SDKs (OpenAI, …)
```

Prompt Engine, Knowledge Engine, Workflow, and Evaluation must not import
vendor SDKs directly.

---

## Folder map

| Path | Role |
|------|------|
| `base.py` | `BaseAIProvider` contract (+ RFC-005 platform methods) |
| `registry.py` | `get_provider`, `ProviderRegistry` |
| `factory.py` | Config-based construction |
| `manager.py` | Selection, logging, retry hooks |
| `capabilities.py` | Capability flags |
| `models.py` | `ModelMetadata`, `UsageReport` |
| `openai.py` / `mock.py` | Production adapters |
| `adapters/*` | Future homes (claude, gemini, …) stubs |

---

## Provider lifecycle

1. Register class on `ProviderRegistry`  
2. `ProviderFactory.create(name)` or `get_provider(name)`  
3. Optional `ProviderManager.generate(...)`  
4. Collect `UsageReport` for Evaluation later  

---

## Extension points

- RFC-003 Workflow — manager-selected providers per stage  
- RFC-004 Evaluation — consume `UsageReport`  
- RFC-006–010 — domain features call platform, not SDKs  

Future: failover, load balancing, automatic selection, Azure/OpenRouter/local.

---

## Example

```python
from content_ai.providers import get_provider
from content_ai.providers.manager import ProviderManager

provider = get_provider('mock')
assert provider.health_check()
print(provider.capabilities())

# Optional platform entry (does not replace existing generation service):
# ProviderManager(default_provider='mock').generate('hello')
```
