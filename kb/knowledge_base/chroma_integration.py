"""Redirect: kb.knowledge_base.chroma_integration → src.library.chroma_integration"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from src.library.chroma_integration import *  # noqa: F401,F403
from src.library.chroma_integration import (
    ChromaIntegration,
    ChromaIntegrationV2,
    get_chroma,
    embed_text,
    embed_batch,
    __all__ as _chroma_all,
)

__all__ = [x for x in _chroma_all if x not in ('__all__',)] + ['ChromaIntegrationV2']

# Register module alias
import src.library.chroma_integration as _mod
sys.modules["kb.knowledge_base.chroma_integration"] = _mod