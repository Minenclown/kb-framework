# Phase 3 Fix: BackupCommand @register_command

**Problem:** BackupCommand in `kb/commands/backup.py` fehlt der `@register_command` Decorator.

## Schritte

### 1. Backup erstellen
```bash
cp ~/projects/kb-framework/kb/commands/backup.py ~/projects/kb-framework/kb/commands/backup.py.bak
```

### 2. Datei prüfen

Suche die Klasse-Deklaration in `backup.py`:
```bash
grep -n "class BackupCommand" ~/projects/kb-framework/kb/commands/backup.py
```

### 3. Decorator hinzufügen

Füge `@register_command` direkt vor der Klassendeklaration ein:

```python
# Vor der Klasse:
@register_command
class BackupCommand(BaseCommand):
```

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from kb.commands.backup import BackupCommand
print('✓ BackupCommand imported')

# Check if decorator registered it
import kb.commands
registry = getattr(kb.commands, '_command_registry', None)
if registry:
    names = [c.name for c in registry]
    if 'backup' in names or 'backup-library' in names:
        print('✓ BackupCommand registered in registry')
"

# Also test CLI
kb backup --help 2>&1 | head -10
```

## Rollback

```bash
# Remove the decorator line
sed -i '/^@register_command$/d' ~/projects/kb-framework/kb/commands/backup.py

# Or restore from backup
cp ~/projects/kb-framework/kb/commands/backup.py.bak \
   ~/projects/kb-framework/kb/commands/backup.py
```

## Checkliste

- [ ] Backup erstellt
- [ ] `@register_command` Decorator hinzugefügt
- [ ] Import für register_command exists (am Anfang der Datei)
- [ ] CLI funktioniert (`kb backup --help`)