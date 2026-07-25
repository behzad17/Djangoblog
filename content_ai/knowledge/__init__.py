"""Knowledge layer package (RFC-002 / RFC-002.5).

Storage, selection, and injection are wired into the production workflow.
Injection remains gated by ENABLE_KNOWLEDGE_* flags (default off).
"""

from content_ai.knowledge.exceptions import (
    KnowledgeEngineError,
    KnowledgeValidationError,
    ManifestError,
)
from content_ai.knowledge.injectors import KnowledgeInjector
from content_ai.knowledge.integration import (
    apply_knowledge_if_enabled,
    prepare_knowledge_for_context,
)
from content_ai.knowledge.models import KnowledgeModule
from content_ai.knowledge.selectors import (
    KeywordSelector,
    KnowledgeSelector,
    get_knowledge_selector,
)
from content_ai.knowledge.utils import (
    load_manifest,
    parse_knowledge_modules,
    validate_manifest,
)

__all__ = [
    'KeywordSelector',
    'KnowledgeEngineError',
    'KnowledgeInjector',
    'KnowledgeModule',
    'KnowledgeSelector',
    'KnowledgeValidationError',
    'ManifestError',
    'apply_knowledge_if_enabled',
    'get_knowledge_selector',
    'load_manifest',
    'parse_knowledge_modules',
    'prepare_knowledge_for_context',
    'validate_manifest',
]
