# Cody Template: Phase 4 - Unbrauchbarer Code

## Kontext
- **Review-Bereich:** Unbrauchbarer Code
- **Zeitbudget:** 8 Minuten
- **Schwellenwerte:**
  - Dead Code: 🔴 REMOVE
  - Alte TODOs: 🟡 FIX_OR_DOCUMENT
  - NotImplementedError: 🔴 IMPLEMENT_OR_REMOVE

---

## Phase 4.1: Dead Code Detection (3 Min)

### Aufgabe
Finde Code der nie aufgerufen wird.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== UNUSED FUNCTIONS (static analysis) ==="
for f in kb/**/*.py src/**/*.py; do
  # Get all function names
  functions=$(grep -oE "^def [a-zA-Z_][a-zA-Z0-9_]*" "$f" | sed 's/^def //')
  for func in $functions; do
    # Skip __init__, __str__, etc
    if [[ "$func" == __* ]]; then continue; fi
    # Count occurrences as calls (not definitions)
    calls=$(grep -c "$func(" "$f" 2>/dev/null || echo 0)
    if [ "$calls" -le 1 ]; then
      echo "POTENTIAL_DEAD: $f:$func (1 occurrence = def only)"
    fi
  done
done

echo -e "\n=== UNUSED CLASSES ==="
for f in kb/**/*.py src/**/*.py; do
  classes=$(grep -oE "^class [a-zA-Z_][a-zA-Z0-9_]*" "$f" | sed 's/^class //' | tr -d ':')
  for cls in $classes; do
    if [[ "$cls" == _* ]]; then continue; fi
    # Check if instantiated
    instantiations=$(grep -c " $cls(" "$f" 2>/dev/null || echo 0)
    if [ "$instantiations" -eq 0 ]; then
      # Check if inherited
      inherits=$(grep -c " $cls\b" "$f" 2>/dev/null || echo 0)
      if [ "$inherits" -le 1 ]; then
        echo "POTENTIAL_DEAD_CLASS: $f:$cls"
      fi
    fi
  done
done

echo -e "\n=== UNUSED IMPORTS ==="
grep -rn "^[from|import]" kb/ src/ --include="*.py" | head -30
```

### Deliverable
- Dead code Liste
- Unused imports

---

## Phase 4.2: Alte TODOs finden (2 Min)

### Aufgabe
Finde TODOs und prüfe它们的 Alter/Relevanz.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== ALL TODOS/FIXMES ==="
grep -rn "TODO\|FIXME\|XXX\|HACK\|BUG\|DEPRECATED" kb/ src/ --include="*.py" -B1

echo -e "\n=== TODO COUNT BY FILE ==="
grep -rn "TODO" kb/ src/ --include="*.py" | awk -F: '{print $1}' | \
  sort | uniq -c | sort -rn

echo -e "\n=== TODOs IN CODE (not tests) ==="
grep -rn "TODO" kb/ src/ --include="*.py" | \
  grep -v "test\|Test\|_test" | head -20
```

### Deliverable
- TODO-Liste mit Locations
- Prioritäts-Vorschläge

---

## Phase 4.3: NotImplementedError Stubs (2 Min)

### Aufgabe
Finde nicht implementierte Methoden.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== NOTIMPLEMENTEDERROR RAISES ==="
grep -rn "NotImplementedError\|raise NotImplemented\|pass  # TODO" kb/ src/ --include="*.py" -B2 -A2

echo -e "\n=== EMPTY FUNCTION BODIES ==="
grep -rn "def .*:$\|def .*:\s*$" kb/ src/ --include="*.py" -A1 | \
  grep -E "def |pass"

echo -e "\n=== STUB METHODS (>1 line) ==="
for f in kb/**/*.py src/**/*.py; do
  grep -n "def .*:" "$f" | while read line; do
    linenum=$(echo "$line" | cut -d: -f1)
    next=$(sed -n "$((linenum+1))p" "$f")
    if echo "$next" | grep -q "pass\|..."; then
      echo "STUB: $f:$line"
    fi
  done
done
```

### Deliverable
- Stub-Liste mit Begründung
- Implementieren oder Entfernen

---

## Phase 4.4: Auskommentierte Blöcke (1 Min)

### Aufgabe
Finde größere auskommentierte Code-Blöcke.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== COMMENTED CODE BLOCKS ==="
for f in kb/**/*.py src/**/*.py; do
  # Count comment lines
  comment_lines=$(grep -c "^\s*#" "$f" 2>/dev/null || echo 0)
  total_lines=$(wc -l < "$f")
  if [ "$comment_lines" -gt 10 ]; then
    ratio=$(echo "scale=2; $comment_lines * 100 / $total_lines" | bc 2>/dev/null || echo "N/A")
    echo "HIGH_COMMENT: $f ($comment_lines comments, ${ratio}%)"
  fi
done

echo -e "\n=== RECENTLY COMMENTED CODE ==="
git -C ~/projects/kb-framework log --all --oneline --source --remotes -- \
  | head -20 2>/dev/null || echo "Git history check skipped"
```

### Deliverable
- Commented blocks report
- Aufräumen-Liste

---

## GATE 4: Entscheidung

### Sofort Entfernen
- [ ] Dead Code:
- [ ] Auskommentierte Blöcke:

### Priorisierte TODOs
- [ ] Diese Woche:
- [ ] Backlog:

### Stub-Aktionen
- [ ] Implementieren:
- [ ] Entfernen:

### Status
```
PHASE_4_STATUS=COMPLETE
DEAD_CODE_FOUND=N
DATE=2026-04-16
```
