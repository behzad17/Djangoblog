"""Source Intelligence package (RFC-006 stub for APF-001).

Passive: no external retrieval. Editors supply URLs/text manually.
"""

from content_ai.source.inspector import SourceInspector
from content_ai.source.models import SourceRecord, create_source_record

__all__ = [
    'SourceInspector',
    'SourceRecord',
    'create_source_record',
]
