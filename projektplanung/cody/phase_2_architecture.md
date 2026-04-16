# Cody Template: Phase 2 - Architektonische Unreinheiten

## Kontext
- **Review-Bereich:** Architektonische Unreinheiten
- **Zeitbudget:** 12 Minuten
- **Schwellenwerte:**
  - Module >500 Zeilen: 🔴 REFACTOR
  - Singleton-Missbrauch: 🟡 ALTERNATIVE
  - SoC-Verletzung: 🔴 DOCUMENT

---

## Phase 2.1: Separation of Concerns (4 Min)

### Aufgabe
Prüfe ob Module für ihre eigentliche Aufgabe verantwortlich sind.

### Commands
```bash
cd ~/projects/kb-framework

# Check responsibilities in key files
echo "=== engine.py responsibilities ==="
head -50 kb/biblio/engine/*.py 2>/dev/null || echo "File structure varies"

echo -e "\n=== sync_manager.py cross-dependencies ==="
grep -n "class\|def \|from\|import" kb/obsidian/sync_manager.py | head -30

echo -e "\n=== config.py business logic check ==="
grep -n "def \|class \|if \|for \|while" kb/base/config.py kb/biblio/config.py 2>/dev/null | \
  grep -v "def __init__\|def load\|def save\|def get\|def set" | head -20
```

### Deliverable
- SoC-Violations Liste
- Verantwortlichkeits-Chaos-Dokumentation

---

## Phase 2.2: Modul-Größen prüfen (3 Min)

### Aufgabe
Identifiziere Module über 500 Zeilen.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== MODULE SIZES (>300 lines) ==="
find kb src -name "*.py" -type f -exec wc -l {} \; | \
  sort -rn | \
  awk '$1 > 300 {print}'

echo -e "\n=== DETAILED ANALYSIS (>500 lines) ==="
find kb src -name "*.py" -type f -exec wc -l {} \; | \
  sort -rn | \
  awk '$1 > 500 {print}'

# Analyze large files for potential splits
echo -e "\n=== CLASS/FUNCTION COUNT IN LARGE FILES ==="
for f in kb/commands/llm.py kb/obsidian/writer.py kb/biblio/content_manager.py kb/obsidian/vault.py kb/obsidian/sync_manager.py; do
  if [ -f "$f" ]; then
    classes=$(grep -c "^class " "$f" 2>/dev/null || echo 0)
    functions=$(grep -c "^def " "$f" 2>/dev/null || echo 0)
    lines=$(wc -l < "$f")
    echo "$f: $lines lines, $classes classes, $functions functions"
  fi
done
```

### Deliverable
- Liste großer Module mit Refactoring-Vorschlägen
- Split-Points identifizieren

---

## Phase 2.3: Singleton-Missbrauch (3 Min)

### Aufgabe
Finde Singleton-Patterns und prüfe ob gerechtfertigt.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== SINGLETON PATTERNS ==="
grep -rn "_instance\|__new__\|Singleton\|_shared\|__instance" kb/ src/ --include="*.py" -B1 -A1

echo -e "\n=== CLASSES WITH SINGLETON PATTERN ==="
for f in kb/**/*.py src/**/*.py; do
  if grep -q "_instance\|_shared" "$f" 2>/dev/null; then
    classes=$(grep -B2 "class " "$f" | grep -E "_instance|_shared" -B5 | grep "^class " | cut -d' ' -f2 | tr -d ':')
    if [ -n "$classes" ]; then
      echo "$f: $classes"
    fi
  fi
done

echo -e "\n=== GLOBAL STATE IN MODULES ==="
grep -rn "^[A-Z_]* = None\|^[A-Z_]* = \{\}\|global [a-z]" kb/ src/ --include="*.py" | head -20
```

### Deliverable
- Singleton-Liste mit Begründung
- Alternative Vorschläge (Dependency Injection, Factory)

---

## Phase 2.4: Kopplungs-Analyse (2 Min)

### Aufgabe
Finde Module mit hoher Fan-Out (zu viele Dependencies).

### Commands
```bash
cd ~/projects/kb-framework

echo "=== FAN-OUT ANALYSIS (>10 imports) ==="
for f in kb/**/*.py src/**/*.py; do
  imports=$(grep -cE "^(from |import )" "$f" 2>/dev/null || echo 0)
  if [ "$imports" -gt 10 ]; then
    echo "HIGH_FANOUT: $f ($imports imports)"
  fi
done

echo -e "\n=== CROSS-MODULE DEPENDENCIES ==="
# kb/ should not deeply depend on specific obsidian internals
grep -rn "from kb.obsidian\|from kb.base\|from kb.commands" kb/biblio kb/scripts --include="*.py" | \
  grep -v "__init__" | head -20

echo -e "\n=== CIRCULAR DEPENDENCY CANDIDATES ==="
# Files that import from each other
for d1 in kb/obsidian kb/biblio kb/commands kb/base; do
  for d2 in kb/obsidian kb/biblio kb/commands kb/base; do
    if [ "$d1" != "$d2" ]; then
      f1=$(ls $d1/*.py 2>/dev/null | head -1)
      if [ -n "$f1" ]; then
        if grep -q "from kb.$d2\|from \.${d2##*/}" "$f1" 2>/dev/null; then
          echo "CROSS: $f1 -> $d2"
        fi
      fi
    fi
  done
done
```

### Deliverable
- Stark gekoppelte Module
- Zirkuläre Abhängigkeits-Kandidaten

---

## GATE 2: Entscheidung

### Kritische Finds (SOFORT)
- [ ] Architecture Blocker:

### Refactoring-Kandidaten
- [ ] Module >500 Zeilen:
- [ ] Singleton-Missbrauch:

### Für später planen
- [ ] Kopplungs-Probleme:
- [ ] SoC-Violations:

### Status
```
PHASE_2_STATUS=COMPLETE
ARCHITECTURE_BLOCKERS=N
DATE=2026-04-16
```
