# Lessons Learned - System Reviews

## 2026-04-27: KB Framework Review (FuClaWork)

### Was funktioniert
- 10-Phasen-Struktur deckt alle Aspekte ab
- Tabellarische Output-Formate sind übersichtlich
- Review-Ergebnisse sind reproduzierbar

### Was verbessert werden muss
- **Templates fehlten** → mussten erst erstellt werden
- **Doku-Update nicht im Workflow** → sollte jeder Phase zugeordnet werden
- **Softaware braucht Handlungsanweisungen** → nicht nur Probleme, sondern Lösungen

### Top-Probleme diesmal
1. Hardcoded Pfade (21 in 8 Dateien) — **Klassiker**
2. Doku veraltet — **Standard-Problem**
3. N+1 Queries — **Performance-Killer**
4. Breite Exception-Handler — **Debugging-Albtraum**
5. Tests failen — **CI/CD-Risiko**

---

## Regeln für zukünftige Reviews

### Vor dem Review
1. **Templates zuerst erstellen** — nicht nach dem Review
2. **Repo-Struktur verstehen** — einlesen bevor man anfängt
3. **Scope klar definieren** — was wird geprüft, was nicht

### Während des Reviews
1. **Jede Phase max. 10-15 Minuten** — sonst verliert man sich
2. **Zwischenergebnisse speichern** — nach jeder Phase
3. **Top-Probleme direkt nummerieren** — nicht erst am Ende
4. **Konkrete Dateipfade notieren** — keine vagen "da irgendwo"

### Nach dem Review
1. **Action Items sofort erstellen** — nicht nur Probleme dokumentieren
2. **Impact/Aufwand abschätzen** — nicht alles ist P1
3. **Für Folgeantworten schreiben** — Softaware braucht Anweisungen, keine Romane
4. **Lessons Learned aktualisieren** — direkt nach Abschluss

---

## Insights für Specialista (zukünftige Reviews)

### Was FuClaWork gut gemacht hat
- Alle 10 Phasen durchgeführt
- Klare Status-Symbole (✅🟡❌)
- Top-Probleme strukturiert

### Was FuClaWork nicht gemacht hat
- Keine konkreten Code-Fixes
- Keine Before/After Beispiele
- Keine Risiko-Mitigation

### Konsequenz für mich
- **Immer konkrete Handlungsanweisungen** statt nur Problembeschreibung
- **Code-Beispiele** wenn möglich
- **Checklisten** für jeden Phase-Fix
- **Prioritäten** nach Impact sortiert

---

## Vorherige Reviews
- (Hier einfügen)
