# Phase 2: BackupCommand @register_command hinzufügen

## Context
BackupCommand fehlt der `@register_command` Decorator.
Er wird daher nicht automatisch in der Command-Registry gefunden.

## Files
- `kb/commands/backup.py`

## Problem
```python
# FEHLT - @register_command
class BackupCommand(BaseCommand):
    name = "backup"
    ...
```

```python
# KORREKT
@register_command
class BackupCommand(BaseCommand):
    name = "backup"
    ...
```

## Steps
1. **Prüfe ob bereits vorhanden**
   ```bash
   rg "@register_command" kb/commands/backup.py
   ```

2. **Falls nicht vorhanden - Decorator hinzufügen**
   - Import prüfen: `from kb.commands.base import register_command`
   - `@register_command` vor Klasse einfügen

3. **Verify**
   ```bash
   kb --help | grep -i backup
   # Sollte "backup" anzeigen
   ```

## Verification
```bash
kb --help
# BackupCommand sollte erscheinen

# Alternativ:
python -c "from kb.commands.backup import BackupCommand; print(BackupCommand.name)"
```

## Rollback
```bash
# Zeile entfernen
sed -i '/^@register_command$/d' kb/commands/backup.py

# Oder:
cd ~/projects/kb-framework && git checkout kb/commands/backup.py
```

## Timeout
5 Minuten