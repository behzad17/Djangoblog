"""Editorial Studio package (ES-000 / ES-001A).

Staff tools for editorial AI features. First tool: Smart News Import.
Does not auto-publish.
"""

from content_ai.editorial_studio.services import NewsImportService

__all__ = ['NewsImportService']
