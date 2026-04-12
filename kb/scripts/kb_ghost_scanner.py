#!/usr/bin/env python3
"""
KB Ghost Scanner – Findet neue Dateien die nicht in KB indexiert sind

Laufzeit: Montag-Freitag 02:00 Uhr (via Cron)
Zweck: Neue Dateien finden und zur KB hinzufügen

Phase 2.3: Erweiterte Extensions + Inkrementelles Scannen
- Extensions: .doc, .docx, .epub hinzugefügt
- Rekursives Scannen tiefer in Unterordner
- Inkrementeller Scan mit Cache
"""

import sqlite3
import os
import json
from pathlib import Path
from datetime import datetime
import csv

# Konfiguration
DB_PATH = Path.home() / ".openclaw" / "kb" / "library" / "biblio.db"
LIBRARY_PATH = Path.home() / "knowledge" / "library"
OUTPUT_DIR = Path.home() / "knowledge" / "library" / "audit"
OUTPUT_FILE = OUTPUT_DIR / "ghost_files.csv"
LOG_FILE = OUTPUT_DIR / "audit_log.md"
CACHE_FILE = Path.home() / ".knowledge" / "ghost_cache.json"

# Zu überwachende Verzeichnisse
SCAN_DIRS = [
    LIBRARY_PATH,
    Path.home() / ".openclaw" / "workspace",
    Path.home() / "knowledge" / "library" / "Gesundheit",
]

# Phase 2.3: Erweiterte Datei-Extensions (mit Warnung für nicht direkt indexierbare)
INDEXABLE_EXTENSIONS = {
    # Dokumente (direkt indexierbar)
    '.pdf', '.txt', '.md', '.html', '.xml',
    # Office (Indexierbar mit Warnung)
    '.doc', '.docx', '.odt', '.rtf',
    # E-Books
    '.epub', '.mobi', '.azw3',
    # Bilder (für OCR-Queue)
    '.jpg', '.jpeg', '.png', '.tiff', '.webp',
    # Code
    '.py', '.sh', '.js', '.ts', '.java', '.c', '.cpp', '.go',
    # Data
    '.json', '.yaml', '.yml', '.csv', '.tsv',
    # Andere
    '.log', '.rst', '.tex',
}

# Warnung bei diesen Extensions (brauchen externe Tools)
EXTERNAL_TOOL_EXTENSIONS = {'.doc', '.docx', '.odt', '.rtf', '.epub', '.mobi', '.azw3'}

def log(message: str):
    """Loggt eine Nachricht"""
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}")

def init_output_dir():
    """Erstellt Output-Verzeichnis wenn nötig"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_indexed_files() -> set:
    """Holt alle in KB indexierte Dateien"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.execute("SELECT DISTINCT file_path FROM files WHERE file_path IS NOT NULL")
    indexed = {row[0] for row in cursor.fetchall()}
    conn.close()
    return indexed

def load_cache() -> dict:
    """Lädt gecachte Datei-Hashes für inkrementelles Scannen"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache: dict):
    """Speichert Cache"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def should_scan_file(file_path: Path, cache: dict, incremental: bool) -> bool:
    """
    Prüfe ob Datei seit letztem Scan geändert.
    Phase 2.3: Inkrementelles Scannen.
    """
    if not incremental:
        return True
    
    key = str(file_path)
    try:
        current_mtime = file_path.stat().st_mtime
        if key not in cache or cache[key] != current_mtime:
            return True
    except:
        pass
    return False

def scan_for_files(incremental: bool = True) -> list[Path]:
    """
    Scannt alle Verzeichnisse nach indexierbaren Dateien.
    
    Phase 2.3: 
    - Rekursives Scannen (rglob statt glob)
    - Inkrementelles Scannen mit Cache
    """
    files = []
    cache = load_cache() if incremental else {}
    new_cache = {}
    
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            log(f"WARN: Verzeichnis existiert nicht: {scan_dir}")
            continue
        
        # Phase 2.3: rglob für rekursives Scannen in Unterordnern
        for ext in INDEXABLE_EXTENSIONS:
            for f in scan_dir.rglob(f"*{ext}"):  # rglob statt glob
                # Skip if should be skipped in incremental mode
                if not should_scan_file(f, cache, incremental):
                    continue
                files.append(f)
                # Update cache
                try:
                    new_cache[str(f)] = f.stat().st_mtime
                except:
                    pass
    
    # Save updated cache
    if incremental:
        save_cache(new_cache)
    
    return files

def find_ghost_files(indexed: set, files: list[Path]) -> list[dict]:
    """Findet Dateien die nicht in KB sind"""
    ghost_files = []
    for f in files:
        str_path = str(f)
        if str_path not in indexed:
            ghost_files.append({
                'path': str_path,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return ghost_files

def save_ghost_files(ghost_files: list[dict]):
    """Speichert Ghost-Dateien als CSV"""
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'size', 'modified'])
        writer.writeheader()
        writer.writerows(ghost_files)
    log(f"Gefunden: {len(ghost_files)} Ghost-Dateien")

def update_log(ghost_count: int):
    """Aktualisiert das Audit-Log"""
    with open(LOG_FILE, 'a') as f:
        f.write(f"\n## {datetime.now():%Y-%m-%d} (Ghost-Scan)\n")
        f.write(f"- Ghost-Dateien gefunden: {ghost_count}\n")

def main(incremental: bool = True):
    log("Start: KB Ghost Scanner")
    init_output_dir()
    
    mode = "incremental" if incremental else "full"
    log(f"Mode: {mode}")
    
    indexed = get_indexed_files()
    log(f"Indexierte Dateien in KB: {len(indexed)}")
    
    files = scan_for_files(incremental=incremental)
    log(f"Gescannte Dateien (neu/geändert): {len(files)}")
    
    ghost_files = find_ghost_files(indexed, files)
    
    # Check for external tool needed
    external_count = sum(1 for g in ghost_files 
                         if any(g['path'].endswith(ext) for ext in EXTERNAL_TOOL_EXTENSIONS))
    
    if ghost_files:
        save_ghost_files(ghost_files)
        update_log(len(ghost_files))
        log(f"Ghost-Dateien gefunden: {len(ghost_files)}")
        log(f"CSV gespeichert: {OUTPUT_FILE}")
        if external_count > 0:
            log(f"⚠️  {external_count} Dateien brauchen externe Tools (docx, epub, etc.)")
    else:
        log("Keine Ghost-Dateien gefunden")
    
    log("Fertig: KB Ghost Scanner")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='KB Ghost Scanner')
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental',
                       help='Scan mode: full (all files) or incremental (changed only)')
    args = parser.parse_args()
    main(incremental=(args.mode == 'incremental'))
