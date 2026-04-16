# Phase 6 Fix: Hardcoded Paths in Scripts

**Problem:** Scripts nutzen hardcoded Home-Paths statt KBConfig.

## Betroffene Dateien

- `kb/scripts/reembed_all.py`
- `kb/scripts/sync_chroma.py`

## Schritte

### 1. reembed_all.py

Aktuell:
```python
db_path = Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"
chroma_path = Path.home() / ".openclaw" / "kb" / ".knowledge" / "chroma_db"
```

Ersetzen mit:
```python
from src.base.config import KBConfig

config = KBConfig.get_instance()
db_path = config.db_path
chroma_path = config.chroma_path  # oder entsprechendes config.attrib
```

### 2. sync_chroma.py

Aktuell:
```python
from config import CHROMA_PATH, DB_PATH
```

Ersetzen mit:
```python
from src.base.config import KBConfig

config = KBConfig.get_instance()
CHROMA_PATH = config.chroma_path
DB_PATH = config.db_path
```

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from src.base.config import KBConfig
config = KBConfig.get_instance()
print(f'db_path: {config.db_path}')
print(f'chroma_path: {config.chroma_path}')

# Test scripts import without error
import sys
sys.path.insert(0, 'kb/scripts')
# Can't actually run them without dependencies, but import check
print('✓ KBConfig imports work')
"
```

## Rollback

```bash
cd ~/projects/kb-framework && git checkout kb/scripts/reembed_all.py kb/scripts/sync_chroma.py
```

## Checkliste

- [ ] reembed_all.py nutzt KBConfig
- [ ] sync_chroma.py nutzt KBConfig
- [ ] Keine Path.home() hardcodes mehr in den Scripts