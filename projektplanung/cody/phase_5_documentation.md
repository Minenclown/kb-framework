# Cody Template: Phase 5 - Dokumentation

## Kontext
- **Review-Bereich:** Dokumentation
- **Zeitbudget:** 8 Minuten
- **Schwellenwerte:**
  - README unvollständig: 🟡 FILL_GAPS
  - Fehlende Docstrings: 🟡 ADD
  - CHANGELOG veraltet: 🔴 UPDATE

---

## Phase 5.1: README Vollständigkeit (3 Min)

### Aufgabe
Prüfe README auf Vollständigkeit.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== README.md ANALYSIS ==="
if [ -f README.md ]; then
  echo "File size: $(wc -c < README.md) bytes"
  echo "Line count: $(wc -l < README.md)"
  echo -e "\n=== SECTIONS PRESENT ==="
  grep -E "^#{1,3} " README.md
  
  echo -e "\n=== CHECKING KEY SECTIONS ==="
  for section in "Installation" "Usage" "Quick Start" "Configuration" "License"; do
    if grep -qi "$section" README.md; then
      echo "✓ $section"
    else
      echo "✗ MISSING: $section"
    fi
  done
  
  echo -e "\n=== CODE BLOCKS ==="
  echo "Fenced code blocks: $(grep -c '```' README.md)"
  echo "Shell commands: $(grep -c 'bash\|shell\|\$' README.md)"
else
  echo "README.md NOT FOUND!"
fi
```

### Deliverable
- README-Vervollständigungs-Plan
- Fehlende Sektionen

---

## Phase 5.2: API-Dokumentation (2 Min)

### Aufgabe
Prüfe Docstrings in öffentlichen APIs.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== FILES WITHOUT DOCSTRINGS ==="
for f in kb/**/*.py; do
  # Check first 10 lines for docstring
  first10=$(head -10 "$f")
  if ! echo "$first10" | grep -q '""\|'\'''; then
    echo "NO_DOCSTRING: $f"
  fi
done

echo -e "\n=== PUBLIC FUNCTIONS WITHOUT DOCSTRINGS ==="
for f in kb/commands/*.py kb/biblio/engine/*.py kb/obsidian/*.py; do
  if [ -f "$f" ]; then
    grep -n "^def " "$f" | while read line; do
      linenum=$(echo "$line" | cut -d: -f1)
      # Check if next non-empty line has docstring
      next=$(sed -n "$((linenum+1))p" "$f" | grep -v '^\s*#' | grep -v '^\s*$')
      if ! echo "$next" | grep -q '""\|'\'''; then
        echo "NO_DOC: $f:$line"
      fi
    done
  fi
done

echo -e "\n=== TYPE HINTS COVERAGE ==="
grep -rn "def \|-> " kb/ --include="*.py" | \
  grep -v "-> None\|-> str\|-> int\|-> bool\|-> dict\|-> list" | \
  grep -v ": $" | head -20
```

### Deliverable
- Documentation gaps
- Type hint coverage report

---

## Phase 5.3: Beispiele funktionsfähig? (2 Min)

### Aufgabe
Prüfe ob Code-Beispiele funktionieren.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== EXAMPLES DIRECTORY ==="
if [ -d examples/ ]; then
  ls -la examples/
  echo -e "\n=== EXAMPLE FILES ==="
  find examples/ -type f | head -10
else
  echo "No examples/ directory"
fi

echo -e "\n=== README CODE BLOCKS ==="
grep -n '```' README.md | head -20

echo -e "\n=== HOW_TO_KB EXAMPLES ==="
if [ -f HOW_TO_KB.md ]; then
  grep -n '```\|kb ' HOW_TO_KB.md | head -20
fi

echo -e "\n=== SCRIPT EXAMPLES ==="
ls kb/scripts/*.py | head -5
```

### Deliverable
- Example validation report
- Funktionsfähige Beispiele dokumentieren

---

## Phase 5.4: CHANGELOG aktuell? (1 Min)

### Aufgabe
Prüfe CHANGELOG auf Aktualität.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== CHANGELOG.md ANALYSIS ==="
if [ -f CHANGELOG.md ]; then
  echo "File size: $(wc -c < CHANGELOG.md) bytes"
  echo "Line count: $(wc -l < CHANGELOG.md)"
  
  echo -e "\n=== FIRST 30 LINES ==="
  head -30 CHANGELOG.md
  
  echo -e "\n=== RECENT ENTRIES ==="
  grep -n "^## \|^### " CHANGELOG.md | head -10
  
  echo -e "\n=== ENTRY COUNT ==="
  echo "Major versions: $(grep -c "^## " CHANGELOG.md)"
  echo "Features/Bugfixes: $(grep -c "^### " CHANGELOG.md)"
else
  echo "CHANGELOG.md NOT FOUND!"
fi

echo -e "\n=== GIT TAGS (if any) ==="
git -C ~/projects/kb-framework tag 2>/dev/null | tail -5 || echo "No tags"

echo -e "\n=== LAST GIT COMMIT ==="
git -C ~/projects/kb-framework log --oneline -5 2>/dev/null || echo "Git check failed"
```

### Deliverable
- CHANGELOG-Audit
- Letzter Eintrag dokumentieren

---

## GATE 5: Abschluss

### Dokumentations-Pflege (Backlog)
- [ ] README erweitern:
- [ ] Docstrings hinzufügen:
- [ ] CHANGELOG aktualisieren:

### Finale Zusammenfassung
```
PHASE_5_STATUS=COMPLETE
DOCUMENTATION_COMPLETE=N
DATE=2026-04-16
```

---

## 📊 FINAL REVIEW SUMMARY

### Kritische Blocker (Sofort beheben)
1. 
2. 
3. 

### Architektur-Probleme (Refactoring planen)
1. 
2. 
3. 

### Optimierungen (bei Gelegenheit)
1. 
2. 

### Aufräumen (Dead Code)
1. 
2. 

### Dokumentation (Backlog)
1. 
2. 

### Gesamtbewertung
- **Strukturelle Fehler:** ⭐⭐⭐⭐⭐ (1-5)
- **Architektur:** ⭐⭐⭐⭐⭐
- **Code-Qualität:** ⭐⭐⭐⭐⭐
- **Dokumentation:** ⭐⭐⭐⭐⭐

**Empfehlung:** [RELEASE|POSTPONE|BREAKING_CHANGE]
