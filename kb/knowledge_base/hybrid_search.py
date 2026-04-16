"""Redirect: kb.knowledge_base.hybrid_search → src.library.hybrid_search"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from src.library.hybrid_search import *  # noqa: F401,F403
from src.library.hybrid_search import (
    HybridSearch,
    SearchResult,
    SearchConfig,
    get_search,
)

import src.library.hybrid_search as _mod
sys.modules["kb.knowledge_base.hybrid_search"] = _mod