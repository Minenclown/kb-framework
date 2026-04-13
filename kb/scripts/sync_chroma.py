#!/usr/bin/env python3
"""ChromaDB Sync Tool - Synchronisiert SQLite mit ChromaDB."""

import argparse
import sqlite3
import sys
from pathlib import Path

# Add kb to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.knowledge_base.chroma_integration import ChromaIntegration
from config import CHROMA_PATH, DB_PATH


def get_sqlite_sections(conn):
    """Holt alle Section IDs aus SQLite."""
    # file_sections hat: id (INTEGER), file_id (INTEGER), section_header, section_content
    cursor = conn.execute(
        "SELECT id, file_id FROM file_sections"
    )
    return {str(row[0]): str(row[1]) for row in cursor.fetchall()}


def get_chroma_sections(chroma_path):
    """Holt alle Section IDs aus ChromaDB."""
    try:
        chroma = ChromaIntegration(chroma_path=chroma_path)
        results = chroma.sections_collection.get(include=[])
        return set(results['ids'])
    except Exception as e:
        print(f"❌ ChromaDB Fehler: {e}")
        return set()


def sync_stats(conn, chroma_path):
    """Zeigt Sync-Statistiken."""
    sqlite_sections = get_sqlite_sections(conn)
    chroma_sections = get_chroma_sections(chroma_path)
    
    sqlite_count = len(sqlite_sections)
    chroma_count = len(chroma_sections)
    
    missing_from_chroma = set(sqlite_sections.keys()) - chroma_sections
    orphans_in_chroma = chroma_sections - set(sqlite_sections.keys())
    
    print(f"📊 Sync Statistiken")
    print(f"  SQLite Sections:   {sqlite_count}")
    print(f"  ChromaDB Sections: {chroma_count}")
    print(f"  Coverage:          {chroma_count/max(sqlite_count,1)*100:.1f}%")
    print(f"  Missing:           {len(missing_from_chroma)}")
    print(f"  Orphans:           {len(orphans_in_chroma)}")
    
    return missing_from_chroma, orphans_in_chroma


def sync_dry_run(conn, chroma_path):
    """Zeigt was synchronisiert werden würde."""
    missing, orphans = sync_stats(conn, chroma_path)
    
    if missing:
        print(f"\n📥 Würde zu ChromaDB hinzufügen: {len(missing)} sections")
    
    if orphans:
        print(f"\n🗑️  Würde aus ChromaDB entfernen: {len(orphans)} orphans")
    
    if not missing and not orphans:
        print(f"\n✅ Alles synchronisiert!")


def sync_execute(conn, chroma_path):
    """Führt die Synchronisation durch."""
    missing, orphans = sync_stats(conn, chroma_path)
    
    if missing:
        print(f"\n📥 Füge {len(missing)} Sections zu ChromaDB hinzu...")
        # TODO: EmbeddingPipeline verwenden um fehlende zu embedden
        print(f"   (Hier würde EmbeddingPipeline.embed_sections() aufgerufen)")
    
    if orphans:
        print(f"\n🗑️  Entferne {len(orphans)} Orphans aus ChromaDB...")
        chroma = ChromaIntegration(chroma_path=chroma_path)
        chroma.sections_collection.delete(ids=list(orphans))
        print(f"   ✅ {len(orphans)} orphans entfernt")
    
    if not missing and not orphans:
        print(f"\n✅ Alles bereits synchronisiert!")


def main():
    parser = argparse.ArgumentParser(description='ChromaDB Sync Tool')
    parser.add_argument('--stats', action='store_true', help='Nur Statistiken anzeigen')
    parser.add_argument('--dry-run', action='store_true', help='Simulation ohne Änderungen')
    parser.add_argument('--execute', action='store_true', help='Synchronisation ausführen')
    
    args = parser.parse_args()
    
    if not any([args.stats, args.dry_run, args.execute]):
        parser.print_help()
        return
    
    # Connect to DB
    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        if args.stats:
            sync_stats(conn, CHROMA_PATH)
        elif args.dry_run:
            sync_dry_run(conn, CHROMA_PATH)
        elif args.execute:
            sync_execute(conn, CHROMA_PATH)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
