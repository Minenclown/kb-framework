"""Redirect module: kb.knowledge_base → src.library

All imports from kb.knowledge_base are redirected to src.library.
This preserves backward compatibility while the codebase migrates
to the new src/ package layout.
"""
import sys
from pathlib import Path

# Ensure src/ is on the import path
_project_root = Path(__file__).parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Register the module alias so that:
#   from kb.knowledge_base.X import Y
# resolves to src.library.X.Y
import src.library
sys.modules["kb.knowledge_base"] = src.library

# Re-export everything from src.library
from src.library import *  # noqa: F401,F403
from src.library import __all__