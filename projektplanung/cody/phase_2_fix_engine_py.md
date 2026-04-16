# Phase 2 Fix: engine.py Methoden und Decorator

**Problem:** EngineListCommand und EngineInfoCommand verwenden `execute()` statt `_execute()`, haben falsche `add_arguments()` Signatur, und haben keinen `@register_command` Decorator.

## Aktuelle Probleme

1. `execute(self, args)` → BaseCommand.run() ruft `_execute()` auf (ohne args)
2. `add_arguments(self, parser)` → Sollte `add_arguments(self, parser: argparse.ArgumentParser)` sein
3. Kein `@register_command` Decorator

## Schritte

### 1. Backup erstellen
```bash
cp ~/projects/kb-framework/kb/commands/engine.py ~/projects/kb-framework/kb/commands/engine.py.bak
```

### 2. Changes anwenden

Ersetze in `kb/commands/engine.py`:

**Decorators hinzufügen:**
```python
# VOR jeder Klasse:
@register_command
class EngineListCommand(BaseCommand):
```

**Methoden umbenennen:**
```python
# execute(self, args) → _execute(self)
def _execute(self) -> int:
```

**add_arguments korrigieren:**
```python
def add_arguments(self, parser: argparse.ArgumentParser):
```

**Beispiel EngineListCommand:**
```python
@register_command
class EngineListCommand(BaseCommand):
    name = "engine-list"
    help = "List available LLM engines"
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Show detailed engine information"
        )
    
    def _execute(self) -> int:
        config = LLMConfig.get_instance()
        engines = _get_engines(config)
        
        for name, engine in engines.items():
            print(f"  {name}")
        
        return 0
```

## Verification

```bash
cd ~/projects/kb-framework

python3 -c "
from kb.commands.engine import EngineListCommand, EngineInfoCommand
print('✓ engine.py classes importable')

# Test class attributes
assert hasattr(EngineListCommand, 'name')
assert hasattr(EngineListCommand, 'add_arguments')
assert hasattr(EngineListCommand, '_execute')
print('✓ EngineListCommand has correct methods')

assert hasattr(EngineInfoCommand, 'name')
assert hasattr(EngineInfoCommand, 'add_arguments')
assert hasattr(EngineInfoCommand, '_execute')
print('✓ EngineInfoCommand has correct methods')
"
```

## Rollback

```bash
# Restore from backup
cp ~/projects/kb-framework/kb/commands/engine.py.bak \
   ~/projects/kb-framework/kb/commands/engine.py

# Or from git
cd ~/projects/kb-framework && git checkout kb/commands/engine.py
```

## Checkliste

- [ ] Backup erstellt
- [ ] `@register_command` bei EngineListCommand
- [ ] `@register_command` bei EngineInfoCommand
- [ ] `execute()` → `_execute()` bei EngineListCommand
- [ ] `execute()` → `_execute()` bei EngineInfoCommand
- [ ] `add_arguments(self, parser)` Signatur korrigiert
- [ ] `_execute()` hat keine args (nur `self`)
- [ ] Verification Tests bestanden