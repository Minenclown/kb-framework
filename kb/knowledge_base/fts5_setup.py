"""Redirect: kb.knowledge_base.fts5_setup → src.library.fts5_setup"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from src.library.fts5_setup import *  # noqa: F401,F403
from src.library.fts5_setup import (
    check_fts5_available,
    setup_fts5,
    rebuild_fts5_index,
    get_fts5_stats,
)

import src.library.fts5_setup as _mod
sys.modules["kb.knowledge_base.fts5_setup"] = _mod