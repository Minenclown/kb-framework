# Cody Template: Phase 1 - Strukturelle Fehler

## Kontext
- **Review-Bereich:** Strukturelle Fehler
- **Zeitbudget:** 10 Minuten
- **Schwellenwerte:** 
  - Zirkuläre Imports: 🔴 SOFORT
  - Orphaned Files: 🟡 ARCHIVE
  - Import-Probleme: 🔴 FIX

---

## Phase 1.1: Zirkuläre Imports prüfen (3 Min)

### Aufgabe
Prüfe auf zirkuläre Import-Ketten im kb-framework.

### Commands
```bash
cd ~/projects/kb-framework

# Quick Import-Test
python3 -c "
import sys
sys.path.insert(0, 'kb')
sys.path.insert(0, 'src')

# Test critical imports
try:
    from kb import commands
    print('✓ commands import OK')
except ImportError as e:
    print(f'✗ commands: {e}')

try:
    from kb.obsidian import vault
    print('✓ vault import OK')
except ImportError as e:
    print(f'✗ vault: {e}')

try:
    from kb.biblio import engine
    print('✓ engine import OK')
except ImportError as e:
    print(f'✗ engine: {e}')
"

# Detailed circular import check
python3 -c "
import ast
import os
from pathlib import Path

def get_imports(filepath):
    with open(filepath) as f:
        try:
            tree = ast.parse(f.read())
            return [node.names[0].name for node in ast.walk(tree) 
                   if isinstance(node, ast.ImportFrom) and node.module]
        except:
            return []

kb_path = Path('kb')
for py_file in kb_path.rglob('*.py'):
    imports = get_imports(py_file)
    for imp in imports:
        if imp.startswith('kb.'):
            print(f'{py_file}: {imp}')
" | sort | uniq
```

### Deliverable
- Liste zirkulärer Import-Ketten
- Fehlermeldungen dokumentieren

---

## Phase 1.2: Fehlende/verwaiste Dateien (3 Min)

### Aufgabe
Finde Python-Dateien, die nicht importiert werden.

### Commands
```bash
cd ~/projects/kb-framework

# List all Python files
echo "=== ALL PYTHON FILES ==="
find kb src -name "*.py" -type f | sort

# Check for __init__.py presence
echo -e "\n=== MISSING __init__.py ==="
for dir in $(find kb src -type d); do
  if [ ! -f "$dir/__init__.py" ]; then
    echo "MISSING: $dir/__init__.py"
  fi
done

# Find potentially orphaned modules
echo -e "\n=== ORPHANED MODULES ==="
find kb src -name "*.py" -type f | while read f; do
  name=$(basename "${f%.py}")
  # Skip __init__ files
  if [ "$name" = "__init__" ]; then continue; fi
  # Check if imported anywhere
  if ! grep -rq "from.*$name\|import $name\|'$name'" kb/ src/ --include="*.py" 2>/dev/null; then
    echo "ORPHAN_CANDIDATE: $f"
  fi
done
```

### Deliverable
- Liste verwaister Dateien
- Fehlende `__init__.py` Dateien

---

## Phase 1.3: Broken Dependencies (2 Min)

### Aufgabe
Prüfe auf fehlende externe Abhängigkeiten.

### Commands
```bash
cd ~/projects/kb-framework

# Extract all external imports
echo "=== EXTERNAL IMPORTS ==="
grep -rh "^from \|^import " kb/ src/ --include="*.py" | \
  grep -v "^from \." | \
  grep -v "^from kb" | \
  grep -v "^from src" | \
  grep -v "^\s*#" | \
  sort -u

# Check requirements.txt completeness
echo -e "\n=== REQUIREMENTS CHECK ==="
if [ -f requirements.txt ]; then
  cat requirements.txt
else
  echo "No requirements.txt found"
fi

if [ -f requirements-transformers.txt ]; then
  echo -e "\n=== TRANSFORMERS REQUIREMENTS ==="
  cat requirements-transformers.txt
fi
```

### Deliverable
- Externe Dependencies Liste
- Fehlende Packages in requirements

---

## Phase 1.4: Import-Reihenfolge (2 Min)

### Aufgabe
Prüfe Import-Sortierung mit isort.

### Commands
```bash
cd ~/projects/kb-framework

# Check if isort is available
if command -v isort &> /dev/null; then
  echo "=== ISORT CHECK ==="
  isort --check-only --diff kb/ src/ 2>&1 | head -50
else
  echo "isort not installed - skipping"
  echo "Install with: pip install isort"
fi

# Manual check for common issues
echo -e "\n=== IMPORT ORDER ISSUES ==="
for f in kb/**/*.py; do
  # Check for imports after code
  python3 -c "
import ast
with open('$f') as fp:
    lines = fp.readlines()
    tree = ast.parse(''.join(lines))
    
    last_import_line = 0
    first_code_line = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('from ') or stripped.startswith('import '):
            last_import_line = i
        elif stripped and not stripped.startswith('#') and not stripped.startswith('\"\"\"') and first_code_line == 0:
            if 'def ' not in stripped and 'class ' not in stripped:
                first_code_line = i
    
    if last_import_line > 0 and first_code_line > last_import_line + 1:
        print(f'$f: Imports after code (line {last_import_line})')
" 2>/dev/null
done
```

### Deliverable
- Import-Reihenfolge-Probleme
- isort-Konfiguration falls nötig

---

## GATE 1: Entscheidung

### Kritische Finds (SOFORT)
- [ ] Zirkuläre Imports gefunden:
- [ ] Broken Dependencies:

### Mittlere Finds (Später)
- [ ] Orphaned Files:
- [ ] Import-Reihenfolge:

### Status
```
PHASE_1_STATUS=COMPLETE
CRITICAL_BLOCKERS=N
DATE=2026-04-16
```
