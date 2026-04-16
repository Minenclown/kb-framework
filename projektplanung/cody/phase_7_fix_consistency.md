# Phase 7 Fix: Consistency Check - @register_command

**Problem:** Einheitliches Pattern für alle Commands.

## Ziel

Alle BaseCommand-Subklassen sollten `@register_command` Decorator haben.

## Zu prüfen

Check alle Commands:
```bash
grep -rn "class.*Command.*BaseCommand" ~/projects/kb-framework/kb/commands/
```

Für jeden Command prüfen:
1. Hat `@register_command` Decorator
2. Nutzt `_execute()` nicht `execute()`
3. Hat korrekte `add_arguments(parser: argparse.ArgumentParser)` Signatur

## Commands zu prüfen

| Command | Decorator | execute→_execute |
|---------|-----------|------------------|
| SyncCommand | ✅ | ✅ |
| AuditCommand | ✅ | ✅ |
| GhostCommand | ❓ | ❓ |
| WarmupCommand | ❓ | ❓ |
| SearchCommand | ✅ | ✅ |
| LLMCommand | ✅ | ✅ |
| BackupCommand | ✅ (Phase 3) | ✅ |
| EngineListCommand | ✅ (Phase 2) | ✅ |
| EngineInfoCommand | ✅ (Phase 2) | ✅ |

## Schritte

### 1. Alle Commands auflisten
```bash
for f in ~/projects/kb-framework/kb/commands/*.py; do
    echo "=== $(basename $f) ==="
    grep -n "class.*Command" "$f"
done
```

### 2. Fehlende fixen

Wenn Commands ohne Decorator gefunden werden:
```python
@register_command
class SomeCommand(BaseCommand):
    ...
```

### 3. Verification

```bash
kb --help 2>&1 | head -30
```

Sollte alle Commands zeigen.

## Rollback

```bash
cd ~/projects/kb-framework && git checkout kb/commands/
```

## Checkliste

- [ ] Alle Commands mit @register_command
- [ ] Alle Commands nutzen _execute()
- [ ] kb --help zeigt alle Commands