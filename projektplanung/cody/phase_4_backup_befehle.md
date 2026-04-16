# Phase 4: Backup-Befehle implementieren

## Ziel
Backup-Befehl der ausschließlich `~/kb/library/` adressiert.

## Konzept
- **Was:** `kb/library/` komplett (content/, agent/, biblio/, user-defined/)
- **Was nicht:** Code, Systemdateien, configs
- **Ziel:** Ein Backup-Befehl = alle wichtigen Daten erfasst

## Implementation

### Datei: `src/commands/backup_library.py` (neu)

```python
"""Backup command for kb/library/ data only."""

import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.base.command import BaseCommand
from src.base.config import KBConfig
from src.base.logger import KBLogger


class BackupLibraryCommand(BaseCommand):
    """Backup kb/library/ directory - data only, no code."""
    
    name = "backup-library"
    description = "Backup kb/library/ data directory"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--output", "-o",
            type=str,
            default=None,
            help="Output path for backup (default: ~/backups/kb-library-YYYY-MM-DD.tar.gz)"
        )
        parser.add_argument(
            "--compression", "-c",
            type=str,
            choices=["gz", "bz2", "xz"],
            default="gz",
            help="Compression type"
        )
    
    def execute(self, args) -> bool:
        config = KBConfig()
        logger = KBLogger().get_logger()
        
        # Source: kb/library/ (data only)
        library_path = Path(config.base_path) / "kb" / "library"
        
        # Default output: ~/backups/
        if args.output:
            output_path = Path(args.output)
        else:
            backup_dir = Path.home() / "backups"
            backup_dir.mkdir(exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_path = backup_dir / f"kb-library-{date_str}.tar.{args.compression}"
        
        if not library_path.exists():
            logger.error(f"Library path not found: {library_path}")
            return False
        
        try:
            # Create tar archive
            mode = f"w:{args.compression}" if args.compression != "gz" else "w:gz"
            with tarfile.open(output_path, mode) as tar:
                tar.add(library_path, arcname="kb-library")
            
            logger.info(f"Backup created: {output_path}")
            logger.info(f"Source: {library_path}")
            
            # Show stats
            size = output_path.stat().st_size
            logger.info(f"Size: {size / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False


def main():
    cmd = BackupLibraryCommand()
    return cmd.run()


if __name__ == "__main__":
    main()
```

### CLI Integration

In `src/__main__.py` oder entsprechende CLI-Datei:

```python
from src.commands.backup_library import BackupLibraryCommand

# Register command
commands = [
    # ... existing commands ...
    BackupLibraryCommand(),
]
```

### Nutzung

```bash
# Default backup
kb backup-library

# Mit custom output
kb backup-library --output ~/my-backups/kb-data.tar.gz

# Mit bz2 compression
kb backup-library --compression bz2
```

## Checkliste
- [ ] `backup_library.py` erstellt in `src/commands/`
- [ ] CLI-Integration vollständig
- [ ] Backup erstellt nur `kb/library/`
- [ ] Keine .py Dateien im Backup (nur wenn user sie selbst reingelegt hat)
- [ ] Kompression funktioniert (gz, bz2, xz)
- [ ] Output-Pfad konfigurierbar

## Verifikation

```bash
# Test backup
kb backup-library --output /tmp/test-backup.tar.gz

# Prüfen was drin ist
tar -tzf /tmp/test-backup.tar.gz | head -20

# Sollte enthalten:
# kb-library/
# kb-library/content/
# kb-library/agent/
# kb-library/biblio/

# Sollte NICHT enthalten:
# kb-library/*.py
```
