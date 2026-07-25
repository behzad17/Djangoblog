"""Knowledge layer package (RFC-001 placeholders + RFC-002 engine).

Storage, selection, and injection are implemented as inactive architecture.
Production generation does not call this package.
"""

from content_ai.knowledge.exceptions import (
    KnowledgeEngineError,
    KnowledgeValidationError,
    ManifestError,
)
from content_ai.knowledge.injectors import KnowledgeInjector
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
    'get_knowledge_selector',
    'load_manifest',
    'parse_knowledge_modules',
    'validate_manifest',
]
