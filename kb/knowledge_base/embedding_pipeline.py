"""Redirect: kb.knowledge_base.embedding_pipeline → src.library.embedding_pipeline"""
import sys
from pathlib import Path

_project_root = Path(__file__).parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from src.library.embedding_pipeline import *  # noqa: F401,F403
from src.library.embedding_pipeline import (
    EmbeddingPipeline,
    SectionRecord,
    EmbeddingJob,
)

import src.library.embedding_pipeline as _mod
sys.modules["kb.knowledge_base.embedding_pipeline"] = _mod