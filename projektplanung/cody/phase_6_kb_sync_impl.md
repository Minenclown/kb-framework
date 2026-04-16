# Phase 6: KB Sync Implementierung (DG-1 Option 1) - GRÖSSTES PROJEKT

## Context
`sync_to_vault()` und `sync_from_vault()` in `kb/obsidian/writer.py` haben `NotImplementedError`.
DG-1 Entscheidung: Bidirektionaler Sync implementieren.

**Aufwand: ~1-2 Tage (6-10 Stunden)**

## Ziel
```
┌─────────────┐         ┌─────────────┐
│  KB CLI     │◄───────►│  Obsidian   │
│  (source)   │   Sync  │  Vault      │
└─────────────┘         └─────────────┘
     │                       │
     ▼                       ▼
┌─────────────┐         ┌─────────────┐
│ biblio.db   │         │ .md files   │
│ (SQLite)    │         │ (markdown)  │
└─────────────┘         └─────────────┘
```

## Files
### Zu ändern:
- `kb/obsidian/writer.py:496-520` - NotImplementedError ersetzen

### Neu zu erstellen:
- `kb/obsidian/vault_reader.py` - Markdown → KB Entry
- `kb/obsidian/sync_manager.py` - Sync Logik

## Data Mapping

### KB Entry → Markdown Frontmatter
```python
entry_to_frontmatter = {
    'title': 'title',
    'authors': 'authors',  # List as YAML list
    'year': 'year',
    'tags': 'tags',
    'abstract': 'abstract',
    'type': 'type',  # article, book, note, etc.
}
```

### Markdown → KB Entry
```python
# Parse frontmatter + content
def parse_markdown(path: Path) -> dict:
    content = path.read_text()
    frontmatter, body = parse_yaml_frontmatter(content)
    return {
        'title': frontmatter.get('title', path.stem),
        'authors': frontmatter.get('authors', []),
        'year': frontmatter.get('year'),
        'tags': frontmatter.get('tags', []),
        'abstract': frontmatter.get('abstract', body[:500]),
        'content': body,
        'source': str(path),
    }
```

## Phases

### Phase 6a: Datenmodell & Sync State (2h)

#### 1. Sync State Tracking
```python
# kb/obsidian/sync_state.py
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class SyncState:
    """Tracks sync state between KB and Vault"""
    kb_last_sync: datetime
    vault_last_sync: datetime
    conflict_resolution: str  # 'kb_wins' | 'vault_wins' | 'manual'
    
    @classmethod
    def load(cls, path: Path) -> 'SyncState':
        """Load from JSON file"""
        
    def save(self, path: Path):
        """Save to JSON file"""
```

#### 2. Conflict Resolution Strategy
```python
# kb/obsidian/conflict.py
from enum import Enum

class ConflictResolution(Enum):
    KB_WINS = "kb_wins"
    VAULT_WINS = "vault_wins"
    MANUAL = "manual"
    KEEP_BOTH = "keep_both"
```

### Phase 6b: Vault Reader implementieren (4h)

#### 3. vault_reader.py
```python
"""Read entries from Obsidian vault"""
from pathlib import Path
from datetime import datetime

class VaultReader:
    """Read .md files from Obsidian vault"""
    
    def __init__(self, vault_path: Path):
        self.vault = vault_path
    
    def read_entry(self, path: Path) -> dict:
        """Read .md file, parse frontmatter + content"""
        content = path.read_text(encoding='utf-8')
        frontmatter, body = self._parse_frontmatter(content)
        return self._to_kb_entry(frontmatter, body, path)
    
    def list_entries(self) -> list[Path]:
        """List all .md files in vault"""
        return list(self.vault.rglob("*.md"))
    
    def get_modified_since(self, since: datetime) -> list[Path]:
        """Find entries modified since last sync"""
        return [p for p in self.list_entries() 
                if datetime.fromtimestamp(p.stat().st_mtime) > since]
    
    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown"""
        # Handle ---frontmatter--- blocks
        ...
    
    def _to_kb_entry(self, frontmatter: dict, body: str, path: Path) -> dict:
        """Convert frontmatter to KB entry format"""
        return {
            'title': frontmatter.get('title', path.stem),
            'authors': frontmatter.get('authors', []),
            'year': frontmatter.get('year'),
            'tags': frontmatter.get('tags', []),
            'abstract': body[:500],
            'content': body,
            'file_path': str(path),
        }
```

### Phase 6c: Sync Manager implementieren (4h)

#### 4. sync_manager.py
```python
"""Bidirectional sync between KB and Obsidian vault"""
from pathlib import Path
from datetime import datetime

class SyncManager:
    """Manage bidirectional sync"""
    
    def __init__(self, kb_connection, vault_path: Path):
        self.kb = kb_connection
        self.vault = vault_path
        self.reader = VaultReader(vault_path)
        self.state = SyncState.load(self.state_file())
    
    def sync_to_vault(self, entry_id: int, vault_path: Path):
        """Write KB entry to Obsidian vault as .md"""
        entry = self.kb.get_entry(entry_id)
        path = vault_path / f"{entry['title']}.md"
        
        frontmatter = self._entry_to_frontmatter(entry)
        content = f"---\n{yaml.dump(frontmatter)}---\n\n{entry['content']}"
        
        path.write_text(content, encoding='utf-8')
        self._touch_sync_marker()
    
    def sync_from_vault(self, path: Path) -> int:
        """Read .md from vault, upsert to KB"""
        entry_data = self.reader.read_entry(path)
        return self.kb.upsert_entry(entry_data)
    
    def bidirectional_sync(self, strategy: ConflictResolution = ConflictResolution.KB_WINS):
        """Full bidirectional sync with conflict resolution"""
        # 1. Get entries modified since last sync
        modified = self.reader.get_modified_since(self.state.vault_last_sync)
        
        # 2. Sync vault → KB (newer entries)
        for path in modified:
            self._sync_single_from_vault(path, strategy)
        
        # 3. Sync KB → Vault (KB entries not in vault)
        kb_entries = self.kb.get_all_entries()
        for entry in kb_entries:
            if not self._exists_in_vault(entry):
                self.sync_to_vault(entry['id'], self.vault)
        
        # 4. Update sync state
        self.state.vault_last_sync = datetime.now()
        self.state.save()
    
    def _sync_single_from_vault(self, path: Path, strategy: ConflictResolution):
        """Sync single file with conflict handling"""
        vault_entry = self.reader.read_entry(path)
        kb_entry = self._find_kb_entry(vault_entry)
        
        if kb_entry is None:
            # New entry from vault
            self.kb.insert_entry(vault_entry)
        else:
            # Conflict detection
            if vault_entry['modified'] > kb_entry['modified']:
                if strategy == ConflictResolution.VAULT_WINS:
                    self.kb.update_entry(kb_entry['id'], vault_entry)
                elif strategy == ConflictResolution.MANUAL:
                    self._flag_conflict(kb_entry, vault_entry)
```

### Phase 6d: Error Handling & Edge Cases (2h)

#### 5. Exception Handling
```python
class VaultSyncError(Exception):
    """Base exception for vault sync"""
    pass

class FilePermissionError(VaultSyncError):
    """Cannot write to vault"""
    pass

class MalformedFrontmatterError(VaultSyncError):
    """Frontmatter cannot be parsed"""
    pass

class MissingRequiredFieldError(VaultSyncError):
    """Required field missing in entry"""
    pass
```

#### 6. Edge Case Handling
- File permission errors → log and continue
- Malformed frontmatter → skip with warning, log to error file
- Missing required fields → use defaults or skip
- Circular references in links → detect and break
- Large files (>1MB) → chunk processing

### Phase 6e: Integrations-Tests (2h)

#### 7. Test Sync
```bash
# Test KB → Vault
kb sync --to-vault --entry-id 123 --vault /path/to/vault

# Test Vault → KB
kb sync --from-vault --vault /path/to/vault

# Test bidirectional
kb sync --bidirectional --vault /path/to/vault --strategy kb_wins

# Dry-run
kb sync --dry-run --vault /path/to/vault
```

## Verification
```bash
# End-to-end test
python -c "
from kb.obsidian.sync_manager import SyncManager
from kb.obsidian.conflict import ConflictResolution

sm = SyncManager(kb_connection, vault_path=Path('/tmp/test_vault'))
sm.bidirectional_sync(strategy=ConflictResolution.KB_WINS)

# Verify:
# 1. KB entries exist in vault as .md
# 2. Vault .md entries exist in KB
# 3. No conflicts (or conflicts flagged in _conflicts/)
"

# CLI integration
kb sync --dry-run --vault /path/to/vault
kb sync --status --vault /path/to/vault
```

## Rollback
```bash
cd ~/projects/kb-framework && git checkout kb/obsidian/writer.py
# Remove new files if they break things
rm -f kb/obsidian/vault_reader.py kb/obsidian/sync_manager.py kb/obsidian/sync_state.py kb/obsidian/conflict.py
```

## Timeout
1-2 Tage (6-10 Stunden) - GRÖSSTES PROJEKT

## Dependencies
- Phase 1 (Bare except) muss done sein für robustes Error Handling
- KBConnection muss funktionieren

## Risks
- Breaking changes für bestehende sync-Users
- Datetime timezone handling
- Large vault handling (1000+ files)
- Concurrent access (file locking)