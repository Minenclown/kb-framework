# Phase 5: Tests

## Ziel
Sicherstellen dass alles funktioniert nach dem Refactor.

## Test-Kategorien

### 1. Struktur-Tests

```bash
# Test: kb/library/ hat keine .py Dateien
find ~/projects/kb-framework/kb/library -name "*.py" -type f
# Erwartet: KEINE AUSGABE

# Test: src/library/ hat die Dateien
ls ~/projects/kb-framework/src/library/
# Erwartet: __init__.py, chroma_integration.py, embedding_pipeline.py, hybrid_search.py, README.md, CHANGELOG.md

# Test: kb/library/biblio/ existiert (umbenannt von llm/)
ls ~/projects/kb-framework/kb/library/biblio/
# Erwartet: Inhalt vom alten llm/
```

### 2. Import-Tests

```bash
cd ~/projects/kb-framework

python3 -c "
# Test imports
from src.library.chroma_integration import ChromaManager
from src.library.embedding_pipeline import EmbeddingPipeline  
from src.library.hybrid_search import HybridSearcher
print('✓ src.library imports OK')
"
```

### 3. Backup-Test

```bash
# Test: Backup-Befehl existiert
kb backup-library --help

# Test: Backup erstellen
kb backup-library --output /tmp/test-backup.tar.gz

# Test: Backup-Inhalt prüfen
tar -tzf /tmp/test-backup.tar.gz | grep -E '\.py$'
# Erwartet: KEINE .py Dateien (außer user hat sie manuell reingelegt)
```

### 4. Integration-Tests

```bash
cd ~/projects/kb-framework

# Alle vorhandenen Tests laufen lassen
python -m pytest tests/ -v --tb=short 2>&1 | head -50
```

### 5. Regression-Tests

```bash
# Prüfen ob alte Imports fehlschlagen (sollten fehlschlagen)
python3 -c "from kb.library.chroma_integration import ChromaManager" 2>&1 | grep -q "ModuleNotFoundError" && echo "✓ Alte Imports funktionieren nicht (korrekt)"
```

## Test-Script

Erstelle `tests/test_library_refactor.py`:

```python
"""Tests for kb/library refactor."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path.home() / "projects" / "kb-framework"


def test_no_py_in_kb_library():
    """kb/library/ should contain no .py files."""
    library_path = PROJECT_ROOT / "kb" / "library"
    py_files = list(library_path.rglob("*.py"))
    assert len(py_files) == 0, f"Found .py files: {py_files}"


def test_src_library_exists():
    """src/library/ should exist with code files."""
    src_lib = PROJECT_ROOT / "src" / "library"
    assert src_lib.exists()
    
    expected_files = [
        "__init__.py",
        "chroma_integration.py", 
        "embedding_pipeline.py",
        "hybrid_search.py",
    ]
    for f in expected_files:
        assert (src_lib / f).exists(), f"Missing: {f}"


def test_imports_work():
    """New imports should work."""
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from src.library.chroma_integration import ChromaManager
    from src.library.embedding_pipeline import EmbeddingPipeline
    from src.library.hybrid_search import HybridSearcher
    
    assert ChromaManager is not None
    assert EmbeddingPipeline is not None
    assert HybridSearcher is not None


def test_biblio_renamed():
    """llm/ should be renamed to biblio/."""
    biblio_path = PROJECT_ROOT / "kb" / "library" / "biblio"
    llm_path = PROJECT_ROOT / "kb" / "library" / "llm"
    
    assert biblio_path.exists(), "biblio/ not found"
    assert not llm_path.exists(), "llm/ should not exist (renamed to biblio/)"


if __name__ == "__main__":
    test_no_py_in_kb_library()
    test_src_library_exists()
    test_imports_work()
    test_biblio_renamed()
    print("✓ All tests passed")
```

## Checkliste

- [ ] Struktur-Tests passen
- [ ] Import-Tests passen
- [ ] Backup-Test passen
- [ ] Integration-Tests passen
- [ ] Regression-Tests passen (alte Imports failen korrekt)

## Final Verification

```bash
cd ~/projects/kb-framework

echo "=== Struktur ==="
find kb/library -name "*.py" 2>/dev/null || echo "✓ Keine .py in kb/library"
ls src/library/*.py

echo "=== Imports ==="
python3 -c "from src.library.chroma_integration import ChromaManager; print('✓ Imports OK')"

echo "=== Backup ==="
kb backup-library --output /tmp/final-test.tar.gz && echo "✓ Backup OK"

echo "=== Alles OK ==="
```
