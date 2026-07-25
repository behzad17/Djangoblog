"""AI Engine configuration placeholders.

Inactive until a future migration wires PromptBuilder into generation.
Does not affect production OpenAI / prompt-template behaviour.
"""

from __future__ import annotations

# Prompt versioning
DEFAULT_PROMPT_VERSION = 'v1'
SUPPORTED_PROMPT_VERSIONS: tuple[str, ...] = ('v1',)

# Style / tone selection
DEFAULT_STYLE = 'news'
SUPPORTED_STYLES: tuple[str, ...] = (
    'news',
    'analysis',
    'educational',
    'friendly',
)

# System modules assembled in this order (before style + output + user).
SYSTEM_MODULE_ORDER: tuple[str, ...] = (
    'identity',
    'audience',
    'writing',
    'output_schema',
)

# Future: provider registry keys, model defaults, feature flags.
FUTURE_AI_PROVIDERS: tuple[str, ...] = ()

# Knowledge Engine / RAG (RFC-002) — all disabled in production.
ENABLE_KNOWLEDGE_ENGINE = False
ENABLE_RAG = False
ENABLE_KNOWLEDGE_INJECTION = False

# Editorial workflow (RFC-003) — architecture only; not wired to production.
ENABLE_EDITORIAL_WORKFLOW = False

# AI evaluation framework (RFC-004) — passive until integrated.
ENABLE_AI_EVALUATION_FRAMEWORK = False

# Fact checking framework (RFC-007) — passive; never auto-approves publish.
ENABLE_FACT_CHECKING_FRAMEWORK = False

FEATURE_FLAGS: dict[str, bool] = {
    # When True, production may call PromptBuilder (not enabled).
    'use_ai_engine_prompt_builder': False,
    # When True, knowledge modules may be retrieved into prompts (not enabled).
    'inject_knowledge_into_prompts': False,
    # When True, structured JSON output schema is enforced (not enabled).
    'structured_json_output': False,
    # RFC-002 mirrors of module-level flags (also False).
    'ENABLE_KNOWLEDGE_ENGINE': ENABLE_KNOWLEDGE_ENGINE,
    'ENABLE_RAG': ENABLE_RAG,
    'ENABLE_KNOWLEDGE_INJECTION': ENABLE_KNOWLEDGE_INJECTION,
    'ENABLE_EDITORIAL_WORKFLOW': ENABLE_EDITORIAL_WORKFLOW,
    'ENABLE_AI_EVALUATION_FRAMEWORK': ENABLE_AI_EVALUATION_FRAMEWORK,
    'ENABLE_FACT_CHECKING_FRAMEWORK': ENABLE_FACT_CHECKING_FRAMEWORK,
}
