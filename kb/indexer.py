#!/usr/bin/env python3
"""
MarkdownIndexer - Indiziert Markdown-Dateien nach Header-Struktur.
Phase 1 der Suchmaschinen-Implementierung.

Plugin-System: IndexingPlugin ABC ermöglicht flexible ChromaDB-Integration.
"""

import hashlib
import json
import logging
import re
import shutil
import sqlite3
import uuid
from abc import ABC, abstractmethod
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Logger für dieses Modul
logger = logging.getLogger(__name__)

# Konstanten
MAX_CONTENT_LENGTH = 200  # Preview-Länge


class IndexingPlugin(ABC):
    """
    Abstract Base Class für Indexing-Plugins.
    
    Plugins werden nach erfolgreicher Indexierung einer Datei aufgerufen
    und ermöglichen flexible Post-Processing-Aktionen (z.B. ChromaDB-Embedding).
    
    Example:
        class ChromaDBPlugin(IndexingPlugin):
            def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
                # Queue für Background-Embedding
                pass
    """
    
    @abstractmethod
    def on_file_indexed(self, file_path: Path, sections: int, file_id: str) -> None:
        """
        Callback nach erfolgreicher Indexierung einer Datei.
        
        Args:
            file_path: Pfad zur indizierten Datei
            sections: Anzahl der indizierten Abschnitte
            file_id: UUID der Datei in der Datenbank
        """
        pass
    
    @abstractmethod
    def on_file_removed(self, file_path: Path) -> None:
        """
        Callback nach Entfernung einer Datei aus dem Index.
        
        Args:
            file_path: Pfad der entfernten Datei
        """
        pass
    
    def on_indexing_complete(self, stats: dict) -> None:
        """
        Optionaler Callback nach vollständiger Indizierung (index_directory, check_and_update).
        
        Args:
            stats: Statistik-Dict mit 'files' und 'sections' Zählern
        """
        pass


class MarkdownIndexer:
    """Indiziert Markdown-Dateien nach Header-Struktur."""

    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$')

    # Stopwords für Keyword-Extraktion
    #
    # Diese Wörter werden bei der Keyword-Extraktion ignoriert.
    # Typische deutsche Füllwörter (Artikel, Konjunktionen, Präpositionen)
    # die keine semantische Bedeutung für die Suche haben.
    #
    # Warum?减少 noise in Suchergebnissen. Bei "Der Baum ist grün"
    # sind "der", "ist" keine nützlichen Keywords - nur "Baum", "grün".
    STOPWORDS = {
        'der', 'die', 'das', 'und', 'oder', 'mit', 'für', 'von', 'auf', 'in', 'zu',
        'ist', 'sind', 'war', 'wurden', 'wird', 'werden', 'kann', 'können',
        'eine', 'einer', 'einem', 'einen', 'als', 'an', 'auch', 'bei', 'bis',
        'durch', 'hat', 'nach', 'nicht', 'nur', 'ob', 'oder', 'sich',
        'sie', 'sind', 'so', 'sowie', 'um', 'unter', 'von', 'vor', 'wenn',
        'wie', 'wird', 'noch', 'schon', 'sehr', 'wurde', 'wurden', 'sein'
    }

    # Umlaut-Mapping für Keyword-Normalisierung
    UMLAUT_MAP = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}

    def __init__(self, db_path: str):
        self.db_path = db_path

    def parse_file(self, file_path: Path) -> List[dict]:
        """
        Parse eine MD-Datei in Abschnitte.

        Headers (# ## ###) definieren Abschnittsgrenzen.
        """
        sections = []
        header_stack: List[tuple] = []  # (level, header_text)
        current_section = {
            'header': None,
            'level': 0,
            'content': [],
            'line_start': 1,
            'parent_header': None,
            'parent_level': 0
        }

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            match = self.HEADER_PATTERN.match(line)

            if match:
                # Vorherigen Abschnitt speichern
                if current_section['header']:
                    sections.append(self._build_section(
                        current_section, file_path, i - 1
                    ))

                level = len(match.group(1))
                header_text = match.group(2).strip()

                # Hierarchie aktualisieren (Pop to parent level)
                header_stack = header_stack[:level - 1]
                parent_header = header_stack[-1][1] if header_stack else None
                parent_level = header_stack[-1][0] if header_stack else 0
                header_stack.append((level, header_text))

                # Neuen Abschnitt starten
                current_section = {
                    'header': header_text,
                    'level': level,
                    'content': [],
                    'line_start': i,
                    'parent_header': parent_header,
                    'parent_level': parent_level
                }
            else:
                current_section['content'].append(line)

        # Letzten Abschnitt speichern
        if current_section['header']:
            sections.append(self._build_section(
                current_section, file_path, len(lines)
            ))

        return sections

    def _build_section(self, section_data: dict, file_path: Path, line_end: int) -> dict:
        """
        Baue einen Abschnitt-Datensatz.

        Erstellt einen fertigen Dict für die Datenbank-Insertion.
        """
        content = ''.join(section_data['content'])
        keywords = self._extract_keywords(content)

        return {
            'file_path': str(file_path),
            'section_header': section_data['header'],
            'section_level': section_data['level'],
            'parent_header': section_data['parent_header'],
            'content_full': content,
            'content_preview': content[:MAX_CONTENT_LENGTH] + '...' if len(content) > MAX_CONTENT_LENGTH else content,
            'line_start': section_data['line_start'],
            'line_end': line_end,
            'word_count': len(content.split()),
            'keywords': keywords,
            'file_hash': self._hash_file(file_path)
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrahiere Keywords aus Text.

        Strategie:
        - Wörter mit 4+ Buchstaben
        - Stopwords entfernen
        - Top 10 nach Häufigkeit
        """
        # Wörter mit 4+ Buchstaben
        words = re.findall(r'\b[a-zA-ZäöüÄÖÜß]{4,}\b', text.lower())
        # Stopwords entfernen
        keywords = [w for w in words if w not in self.STOPWORDS]
        # Top 10 nach Häufigkeit
        return [k for k, _ in Counter(keywords).most_common(10)]

    def _hash_file(self, file_path: Path) -> str:
        """Berechne MD5-Hash der Datei."""
        return hashlib.md5(file_path.read_bytes()).hexdigest()

    def _categorize_file(self, path: Path) -> str:
        """
        Kategorisiere Datei basierend auf Pfad/Name.

        Kategorien: learnings, adr, briefing, projektplanung, dokumentation
        """
        name = path.name.lower()
        parent = path.parent.name
        path_str = str(path)

        if 'learnings' in parent or 'learning' in name:
            return 'learnings'
        elif 'adr' in name or 'architecture' in parent:
            return 'adr'
        elif 'briefing' in name:
            return 'briefing'
        elif 'projektplanung' in path_str:
            return 'projektplanung'
        return 'dokumentation'

    def _normalize_keyword(self, keyword: str) -> str:
        """
        Normalisiere Keyword (lowercase, Umlaute ersetzen).

        Beispiel: 'Ärger' -> 'aerger'
        """
        normalized = keyword.lower()
        for k, v in self.UMLAUT_MAP.items():
            normalized = normalized.replace(k, v)
        return normalized


class BiblioIndexer:
    """
    Vollständiger Indexer mit Datenbank-Anbindung und Plugin-System.
    
    Unterstützt Context-Manager-Protokoll für automatisches Schließen.
    
    Plugin-System ermöglicht flexible Post-Processing-Aktionen wie ChromaDB-Embedding.

    Example:
        with BiblioIndexer("knowledge.db", plugins=[ChromaDBPlugin()]) as indexer:
            indexer.index_file("test.md")
        # → SQLite + ChromaDB (automatic via plugin)
    """

    def __init__(self, db_path: str, plugins: List[IndexingPlugin] = None):
        """
        Initialisiere BiblioIndexer mit Datenbank-Verbindung.

        Args:
            db_path: Pfad zur SQLite-Datenbank
            plugins: Optional list of IndexingPlugin instances

        Raises:
            FileNotFoundError: Wenn das Datenbank-Verzeichnis nicht existiert
            sqlite3.Error: Bei Datenbank-Verbindungsfehlern
        """
        self.db_path = db_path
        self.plugins = plugins or []

        # Validierung: Datenbank-Verzeichnis muss existieren
        db_dir = Path(db_path).parent
        if db_dir and not db_dir.exists():
            raise FileNotFoundError(
                f"Datenbank-Verzeichnis nicht gefunden: {db_dir}\n"
                f"Bitte erstelle das Verzeichnis oder prüfe den Pfad."
            )

        self.indexer = MarkdownIndexer(db_path)
        self.conn = sqlite3.connect(db_path)
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_check")  # Verify FK mode
        self.conn.row_factory = sqlite3.Row

        # Create embeddings tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY,
                section_id TEXT UNIQUE NOT NULL,
                file_id TEXT,
                model TEXT DEFAULT 'all-MiniLM-L6-v2',
                dimension INTEGER DEFAULT 384,
                embedding_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (section_id) REFERENCES file_sections(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_section_id ON embeddings(section_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_file_id ON embeddings(file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_hash ON embeddings(embedding_hash)")
        self.conn.commit()

    def __enter__(self):
        """Context-Manager Entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context-Manager Exit - schließt DB-Verbindung."""
        self.close()
        return False

    def remove_file(self, file_path: str) -> bool:
        """
        Entferne eine Datei aus dem Index.

        Löscht alle zugehörigen Abschnitte (CASCADE) und Datei-Eintrag.
        """
        try:
            # Hole file_id
            file_id = self.conn.execute(
                "SELECT id FROM files WHERE file_path = ?",
                (file_path,)
            ).fetchone()

            if not file_id:
                logger.warning(f"Datei nicht gefunden: {file_path}")
                return False

            file_id = file_id[0]
            
            # Abschnitte löschen (erst section_keywords, dann file_sections)
            self.conn.execute(
                "DELETE FROM section_keywords WHERE section_id IN (SELECT id FROM file_sections WHERE file_id = ?)",
                (file_id,)
            )
            self.conn.execute(
                "DELETE FROM file_sections WHERE file_id = ?",
                (file_id,)
            )
            self.conn.execute(
                "DELETE FROM files WHERE file_path = ?",
                (file_path,)
            )
            self.conn.commit()
            logger.info(f"🗑️  Entfernt: {file_path}")
            
            # Plugin-Callbacks
            for plugin in self.plugins:
                try:
                    plugin.on_file_removed(Path(file_path))
                except Exception as e:
                    logger.warning(f"Plugin {plugin.__class__.__name__} on_file_removed failed: {e}")
            
            return True
        except Exception as e:
            logger.error(f"⚠️  Fehler beim Entfernen: {e}")
            return False

    def get_embedding_hash(self, embedding) -> str:
        """Berechnet SHA256-Hash eines Embedding-Vektors."""
        import hashlib
        import json
        vec_str = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
        return hashlib.sha256(vec_str.encode()).hexdigest()

    def close(self):
        """Schließe Datenbank-Verbindung."""
        self.conn.close()

    def _get_or_create_keyword(self, keyword: str) -> Optional[str]:
        """Hole oder erstelle Keyword-Eintrag."""
        normalized = self.indexer._normalize_keyword(keyword)

        existing = self.conn.execute(
            "SELECT id FROM keywords WHERE normalized = ?",
            (normalized,)
        ).fetchone()

        if existing:
            self.conn.execute(
                "UPDATE keywords SET usage_count = usage_count + 1 WHERE id = ?",
                (existing['id'],)
            )
            return existing['id']

        keyword_id = str(uuid.uuid4())
        self.conn.execute("""
            INSERT INTO keywords (id, keyword, normalized, usage_count)
            VALUES (?, ?, ?, 1)
        """, (keyword_id, keyword, normalized))
        return keyword_id

    def index_file(self, file_path: Path) -> int:
        """
        Indiziere eine einzelne Datei.

        Args:
            file_path: Pfad zur .md Datei

        Returns:
            Anzahl indizierter Abschnitte (0 wenn unverändert)
        """
        if not file_path.exists() or not file_path.name.endswith('.md'):
            return 0

        current_hash = self.indexer._hash_file(file_path)

        # Prüfe ob sich etwas geändert hat
        existing = self.conn.execute(
            "SELECT id, file_hash FROM files WHERE file_path = ?",
            (str(file_path),)
        ).fetchone()

        if existing and existing['file_hash'] == current_hash:
            logger.debug(f"⏭️  Unverändert: {file_path.name}")
            return 0

        # Alte Einträge löschen (CASCADE kümmert sich um section_keywords)
        file_id = existing['id'] if existing else None
        if file_id:
            self.conn.execute(
                "DELETE FROM file_sections WHERE file_id = ?",
                (file_id,)
            )
        self.conn.execute(
            "DELETE FROM files WHERE file_path = ?",
            (str(file_path),)
        )

        # Datei-Stammdaten
        file_id = str(uuid.uuid4())
        category = self.indexer._categorize_file(file_path)
        content = file_path.read_text(encoding='utf-8')
        line_count = len(content.splitlines())

        self.conn.execute("""
            INSERT INTO files
            (id, file_path, file_name, file_category, file_type,
             file_size, line_count, file_hash, last_modified, index_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'indexed')
        """, (
            file_id,
            str(file_path),
            file_path.name,
            category,
            file_path.suffix[1:],
            file_path.stat().st_size,
            line_count,
            current_hash,
            datetime.fromtimestamp(file_path.stat().st_mtime)
        ))

        # Abschnitte indizieren
        sections = self.indexer.parse_file(file_path)
        section_id_map: dict = {}  # header -> id für FK

        for section in sections:
            section_id = str(uuid.uuid4())
            section_id_map[section['section_header']] = section_id

            # Parent-ID auflösen
            parent_section_id = None
            if section.get('parent_header') and section['parent_header'] in section_id_map:
                parent_section_id = section_id_map[section['parent_header']]

            self.conn.execute("""
                INSERT INTO file_sections
                (id, file_id, section_level, section_header, parent_section_id,
                 content_preview, content_full, line_start, line_end,
                 keywords, word_count, file_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                section_id,
                file_id,
                section['section_level'],
                section['section_header'],
                parent_section_id,
                section['content_preview'],
                section['content_full'],
                section['line_start'],
                section['line_end'],
                json.dumps(section['keywords']),
                section['word_count'],
                current_hash
            ))

            # Keywords in section_keywords eintragen
            for keyword in section['keywords']:
                keyword_id = self._get_or_create_keyword(keyword)
                if keyword_id:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO section_keywords
                        (section_id, keyword_id, weight)
                        VALUES (?, ?, 1.0)
                    """, (section_id, keyword_id))

        self.conn.commit()
        logger.info(f"✅ {file_path.name}: {len(sections)} Abschnitte")
        
        # Plugin-Callbacks nach erfolgreicher Indexierung
        for plugin in self.plugins:
            try:
                plugin.on_file_indexed(Path(file_path), len(sections), file_id)
            except Exception as e:
                logger.warning(f"Plugin {plugin.__class__.__name__} on_file_indexed failed: {e}")
        
        return len(sections)

    def index_directory(self, dir_path: str, recursive: bool = True) -> dict:
        """
        Indiziere alle .md-Dateien in einem Verzeichnis.

        Args:
            dir_path: Verzeichnis-Pfad
            recursive: Auch Unterverzeichnisse durchsuchen

        Returns:
            Dict mit 'files' und 'sections' Zählern
        """
        path = Path(dir_path)
        if not path.exists():
            logger.warning(f"⚠️  Verzeichnis nicht gefunden: {dir_path}")
            return {'files': 0, 'sections': 0}

        pattern = "**/*.md" if recursive else "*.md"
        md_files = list(path.glob(pattern))

        stats = {'files': 0, 'sections': 0}

        for md_file in sorted(md_files):
            sections = self.index_file(md_file)
            if sections > 0:
                stats['files'] += 1
                stats['sections'] += sections

        # Plugin-Callbacks nach abgeschlossener Indexierung
        for plugin in self.plugins:
            try:
                if hasattr(plugin, 'on_indexing_complete'):
                    plugin.on_indexing_complete(stats)
            except Exception as e:
                logger.warning(f"Plugin {plugin.__class__.__name__} on_indexing_complete failed: {e}")

        return stats

    def full_reindex(self, root_paths: List[str]) -> dict:
        """
        Vollständige Neu-Indizierung aller Dateien.

        Args:
            root_paths: Liste von Verzeichnissen zum Indizieren

        Returns:
            Aggregierte Statistik
        """
        total_stats = {'files': 0, 'sections': 0}

        for root in root_paths:
            logger.info(f"\n📂 Indiziere: {root}")
            stats = self.index_directory(root)
            total_stats['files'] += stats['files']
            total_stats['sections'] += stats['sections']

        return total_stats

    def check_and_update(self, watch_paths: List[str]) -> dict:
        """
        Prüfe auf Änderungen und aktualisiere nur bei Bedarf.

        Echte Delta-Index Logik:
        - Vergleicht file_hash mit gespeichertem Hash
        - Indexiert nur geänderte Dateien
        - Löscht entfernte Dateien aus dem Index

        Args:
            watch_paths: Liste von Verzeichnissen zu überwachen

        Returns:
            Dict mit Statistik (files_updated, files_removed, sections)
        """
        stats = {'files_updated': 0, 'files_removed': 0, 'sections': 0}

        for watch_path in watch_paths:
            path = Path(watch_path)
            if not path.exists():
                logger.warning(f"⚠️  Watch-Path nicht gefunden: {watch_path}")
                continue

            # Aktuelle .md Dateien sammeln
            md_files = {str(f): f for f in path.glob("**/*.md")}

            # Already indexed files holen
            indexed_files = {}
            cursor = self.conn.execute(
                "SELECT file_path, file_hash FROM files"
            )
            for row in cursor.fetchall():
                indexed_files[row['file_path']] = row['file_hash']

            # Check für Updates (geänderte oder neue Dateien)
            for file_path, abs_path in md_files.items():
                if not abs_path.exists():
                    continue

                current_hash = self.indexer._hash_file(abs_path)

                if file_path not in indexed_files:
                    # Neue Datei - indexieren
                    logger.info(f"🆕 Neu: {abs_path.name}")
                    sections = self.index_file(abs_path)
                    if sections > 0:
                        stats['files_updated'] += 1
                        stats['sections'] += sections

                elif indexed_files[file_path] != current_hash:
                    # Geänderte Datei - reindexieren
                    logger.info(f"🔄 Geändert: {abs_path.name}")
                    sections = self.index_file(abs_path)
                    if sections > 0:
                        stats['files_updated'] += 1
                        stats['sections'] += sections

            # Entfernte Dateien finden und löschen
            for indexed_path in indexed_files:
                if indexed_path not in md_files:
                    logger.info(f"🗑️  Entfernt: {Path(indexed_path).name}")
                    self.remove_file(indexed_path)
                    stats['files_removed'] += 1

        logger.info(f"📊 Delta-Index: {stats['files_updated']} aktualisiert, "
                   f"{stats['files_removed']} entfernt, {stats['sections']} Abschnitte")
        
        # Plugin-Callbacks nach abgeschlossener Delta-Indexierung
        for plugin in self.plugins:
            try:
                if hasattr(plugin, 'on_indexing_complete'):
                    plugin.on_indexing_complete(stats)
            except Exception as e:
                logger.warning(f"Plugin {plugin.__class__.__name__} on_indexing_complete failed: {e}")
        
        return stats

    def index_unindexed(self, unindexed_dir: str = "unindexed") -> dict:
        """
        Indexiert Dateien aus dem unindexed/ Ordner.

        Diese Methode findet alle Dateien im unindexed/ Verzeichnis
        und indexiert sie automatisch in die Datenbank.

        Args:
            unindexed_dir: Pfad zum unindexed Verzeichnis (relativ oder absolut)

        Returns:
            Dict mit 'files' und 'sections' Zählern
        """
        unindexed_path = Path(unindexed_dir)

        if not unindexed_path.exists():
            logger.info(f"📁 Unindexed-Verzeichnis nicht gefunden: {unindexed_dir}")
            return {'files': 0, 'sections': 0}

        # Finde alle .md Dateien
        md_files = list(unindexed_path.glob("*.md"))

        if not md_files:
            logger.info(f"📁 Keine .md Dateien in {unindexed_dir}")
            return {'files': 0, 'sections': 0}

        logger.info(f"📂 {len(md_files)} Dateien zum Indexieren gefunden")

        stats = {'files': 0, 'sections': 0}

        for md_file in sorted(md_files):
            # Verschiebe in das entsprechende Zielverzeichnis
            # Annahme: unindexed/ enthält strukturierte Dateien
            target_path = Path("projektplanung") / md_file.name

            # Indexiere die Datei
            sections = self.index_file(md_file)

            if sections > 0:
                stats['files'] += 1
                stats['sections'] += sections

                # Optional: Verschiebe indizierte Datei
                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(md_file), str(target_path))
                    logger.info(f"📦 Verschoben: {md_file.name} -> {target_path}")
                except Exception as e:
                    logger.warning(f"⚠️  Verschieben fehlgeschlagen: {e}")

        return stats


def main():
    """CLI für Indexer."""
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "knowledge.db"

    # Logging konfigurieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    indexer = BiblioIndexer(db_path)

    # Default-Pfade falls keine angegeben
    root_paths = [
        "projektplanung",
        "learnings",
    ]

    if len(sys.argv) > 2:
        root_paths = sys.argv[2:]

    logger.info(f"🔍 Starte Indizierung in {db_path}")
    logger.info(f"   Verzeichnisse: {', '.join(root_paths)}\n")

    stats = indexer.full_reindex(root_paths)

    logger.info(f"\n📊 Ergebnis: {stats['files']} Dateien, {stats['sections']} Abschnitte indiziert")

    indexer.close()


if __name__ == "__main__":
    main()
