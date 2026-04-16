# Cody Template: Phase 3 - Optimierbarer Code

## Kontext
- **Review-Bereich:** Optimierbarer Code
- **Zeitbudget:** 10 Minuten
- **Schwellenwerte:**
  - Redundante Berechnungen: 🟡 OPTIMIZE
  - Batching-Möglichkeiten: 🟢 QUICK_WIN
  - Caching-Potenzial: 🟡 EVALUATE

---

## Phase 3.1: Redundante Berechnungen (3 Min)

### Aufgabe
Finde mehrfach ausgeführte Berechnungen.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== LOOP ANALYSIS (nested loops) ==="
for f in kb/**/*.py src/**/*.py; do
  # Count nested loops
  loops=$(grep -c "for .* in .*:\|while .*:" "$f" 2>/dev/null || echo 0)
  if [ "$loops" -gt 3 ]; then
    echo "DEEP_LOOPS: $f ($loops loops)"
  fi
done

echo -e "\n=== FUNCTION CALLS IN LOOPS ==="
# Look for expensive operations in loops
grep -rn "for \|while " kb/ src/ --include="*.py" -A3 | \
  grep -E "chroma|embed|search|query|fetch" | \
  head -20

echo -e "\n=== DUPLICATE CALCULATIONS ==="
# Check for repeated same calculations
grep -rn "\.lower()\|\.upper()\|len(" kb/ src/ --include="*.py" | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | \
  awk '$1 > 5 {print}'
```

### Deliverable
- Redundancy report mit Locations
- Quick-fix Vorschläge

---

## Phase 3.2: Batching-Möglichkeiten (3 Min)

### Aufgabe
Finde Operationen die gebatcht werden könnten.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== DATABASE QUERIES IN LOOPS ==="
grep -rn "for .* in\|while .*:" kb/ src/ --include="*.py" -B1 -A5 | \
  grep -E "cursor|execute|fetch|SELECT|INSERT" | \
  head -30

echo -e "\n=== CHROMA OPERATIONS SEQUENCE ==="
grep -rn "chromadb\|ChromaClient\|collection" kb/ src/ --include="*.py" | \
  grep -v "import\|from" | head -30

echo -e "\n=== FILE I/O IN LOOPS ==="
grep -rn "open(\|with.*open\|Path(" kb/ src/ --include="*.py" | \
  grep -B2 "for \|while " | head -20

echo -e "\n=== ASYNC OPPORTUNITIES ==="
grep -rn "async def\|await " kb/ src/ --include="*.py" | wc -l
grep -rn "\.run_in_executor\|\.to_thread" kb/ src/ --include="*.py" | head -10
```

### Deliverable
- Batching-Vorschläge
- Async-Opportunities

---

## Phase 3.3: Caching-Potenzial (2 Min)

### Aufgabe
Finde Daten die gecacht werden könnten.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== EXPENSIVE COMPUTATIONS ==="
grep -rn "embedding\|rerank\|similarity\|cosine" kb/ src/ --include="*.py" | \
  grep -v "import\|class \|def \|#" | head -20

echo -e "\n=== CONFIG LOADING (potential cache) ==="
grep -rn "load_config\|get_config\|read_config\|\.get\(" kb/ --include="*.py" | \
  grep -v "dict\|\[" | head -20

echo -e "\n=== FILE STATS (potential cache) ==="
grep -rn "stat\|mtime\|exists\|is_file" kb/ src/ --include="*.py" | \
  grep -v "import\|#" | head -15

echo -e "\n=== LRU CACHE PATENTIAL ==="
grep -rn "lru_cache\|cache\|@cache\|functools" kb/ src/ --include="*.py"
```

### Deliverable
- Caching-Empfehlungen
- Memoization-Kandidaten

---

## Phase 3.4: Unnötige Zwischenschritte (2 Min)

### Aufgabe
Finde überflüssige Abstraktionen.

### Commands
```bash
cd ~/projects/kb-framework

echo "=== SINGLE-USE WRAPPER FUNCTIONS ==="
for f in kb/**/*.py src/**/*.py; do
  grep -E "^def " "$f" | while read line; do
    name=$(echo "$line" | sed 's/def \([^(]*\).*/\1/')
    # Count usages
    usages=$(grep -c "$name(" "$f" 2>/dev/null || echo 0)
    if [ "$usages" -le 1 ]; then
      echo "SINGLE_USE: $f:$name (used $usages time)"
    fi
  done
done

echo -e "\n=== IDENTITY WRAPPERS ==="
# Functions that just return/pass through
grep -rn "return .*\|pass$" kb/ src/ --include="*.py" -B2 | \
  grep "def \|return" | head -20

echo -e "\n=== DEAD VARIABLE ASSIGNMENT ==="
grep -rn "= .*#\|= None$" kb/ src/ --include="*.py" | \
  grep -v "if \|for \|while \|def \|class " | head -15
```

### Deliverable
- Simplification-Vorschläge
- Wrapper-Eliminierung

---

## GATE 3: Entscheidung

### Quick Wins (Sofort)
- [ ] Batching-Möglichkeiten:
- [ ] Unnötige Zwischenschritte:

### Für später planen
- [ ] Redundante Berechnungen:
- [ ] Caching-Potenzial:

### Status
```
PHASE_3_STATUS=COMPLETE
QUICK_WINS=N
DATE=2026-04-16
```
