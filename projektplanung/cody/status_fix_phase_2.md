# Fix Phase 2 Status
**Phase:** 2 - engine.py Methoden und Decorator fixen
**Status:** ✅ COMPLETED
**Time:** 2026-04-16 18:02 UTC

## Was wurde gemacht
- `@register_command` Decorator für EngineListCommand und EngineInfoCommand hinzugefügt
- `execute(self, args)` → `_execute(self)` für beide Commands
- `add_arguments(self, parser)` → `add_arguments(self, parser: argparse.ArgumentParser) -> None`
- `args` Referenzen → `self._args` in EngineInfoCommand
- Command-Namen: `"list"` → `"engine-list"`, `"info"` → `"engine-info"` (vermeidet Namenskonflikte)
- `import argparse` und `from kb.commands import register_command` hinzugefügt

## Verifikation
- Syntax-Check: ✅
- BaseCommand Interface-Konformität: ✅

## Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/commands/engine.py
```