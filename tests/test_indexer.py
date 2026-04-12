#!/usr/bin/env python3
"""
Tests for KB Framework - BiblioIndexer
"""

import unittest
import tempfile
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add kb_framework to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from kb.indexer import BiblioIndexer, MarkdownIndexer


class TestMarkdownIndexer(unittest.TestCase):
    """Tests for MarkdownIndexer class."""
    
    def setUp(self):
        """Create temp test file."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_md = Path(self.temp_dir) / "test.md"
        self.test_md.write_text("""# Header 1
Content of section 1.

## Sub Header
More content here.

### Deep Header
Even deeper content.
""")
        self.db_path = Path(self.temp_dir) / "test.db"
    
    def test_parse_file(self):
        """Test parsing a markdown file."""
        indexer = MarkdownIndexer(str(self.db_path))
        sections = indexer.parse_file(self.test_md)
        
        # Should have 3 sections (3 headers)\n        self.assertEqual(len(sections), 3)
        
        # Check first section\n        self.assertEqual(sections[0]['section_header'], 'Header 1')
        self.assertEqual(sections[0]['section_level'], 1)
        self.assertIn('Content of section 1', sections[0]['content_full'])
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        indexer = MarkdownIndexer(str(self.db_path))
        text = "Dies ist ein Test mit vielen interessanten Wörtern"
        keywords = indexer._extract_keywords(text)
        
        # Should filter stopwords\n        self.assertNotIn('und', keywords)
        self.assertNotIn('ist', keywords)
        # Should include meaningful words
        self.assertIn('test', keywords)
    
    def test_hash_file(self):
        """Test file hashing."""
        indexer = MarkdownIndexer(str(self.db_path))
        hash1 = indexer._hash_file(self.test_md)
        hash2 = indexer._hash_file(self.test_md)
        
        # Same file should produce same hash
        self.assertEqual(hash1, hash2)
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestBiblioIndexer(unittest.TestCase):
    """Tests for BiblioIndexer class."""
    
    def setUp(self):
        """Create temp test database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        # Create schema
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_category TEXT,
                file_type TEXT,
                file_size INTEGER,
                line_count INTEGER,
                file_hash TEXT,
                last_modified TIMESTAMP,
                index_status TEXT DEFAULT 'pending'
            );
            
            CREATE TABLE IF NOT EXISTS file_sections (
                id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                section_level INTEGER DEFAULT 1,
                section_header TEXT,
                parent_section_id TEXT,
                content_preview TEXT,
                content_full TEXT,
                line_start INTEGER,
                line_end INTEGER,
                keywords TEXT,
                word_count INTEGER,
                file_hash TEXT,
                importance_score REAL DEFAULT 0.5,
                last_indexed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files(id),
                FOREIGN KEY (parent_section_id) REFERENCES file_sections(id)
            );
            
            CREATE TABLE IF NOT EXISTS keywords (
                id TEXT PRIMARY KEY,
                keyword TEXT UNIQUE NOT NULL,
                normalized TEXT UNIQUE NOT NULL,
                usage_count INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS section_keywords (
                section_id TEXT NOT NULL,
                keyword_id TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                PRIMARY KEY (section_id, keyword_id),
                FOREIGN KEY (section_id) REFERENCES file_sections(id),
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            );
        """)
        self.conn.close()
        
        # Create test markdown file
        self.test_md = Path(self.temp_dir) / "test_section.md"
        self.test_md.write_text("""# Main Header
This is the main content.

## Sub Section
Sub content with important keywords.
""")
    
    def test_index_file(self):
        """Test indexing a file."""
        indexer = BiblioIndexer(str(self.db_path))
        sections = indexer.index_file(self.test_md)
        
        self.assertGreater(sections, 0)
    
    def test_remove_file(self):
        """Test removing a file from index."""
        indexer = BiblioIndexer(str(self.db_path))
        indexer.index_file(self.test_md)
        
        # Remove file
        result = indexer.remove_file(str(self.test_md))
        self.assertTrue(result)
        
        # Verify removal
        cursor = indexer.conn.execute(
            "SELECT COUNT(*) FROM files WHERE file_path = ?",
            (str(self.test_md),)
        )
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
    
    def test_check_and_update_delta(self):
        """Test delta indexing - only changed files."""
        indexer = BiblioIndexer(str(self.db_path))
        
        # Initial index
        indexer.index_file(self.test_md)
        
        # Should return no changes since file hasn't changed
        result = indexer.check_and_update([self.temp_dir])
        
        # Delta index should not trigger full reindex
        self.assertIn('files_updated', result)
        self.assertIn('files_removed', result)
    
    def tearDown(self):
        """Clean up temp files."""
        import shutil
        shutil.rmtree(self.temp_dir)


class TestSearchConfig(unittest.TestCase):
    """Tests for search configuration."""
    
    def test_default_weights(self):
        """Test default search weights."""
        from kb.library.knowledge_base.hybrid_search import SearchConfig
        
        config = SearchConfig()
        
        # Should have balanced weights
        self.assertEqual(config.semantic_weight, 0.60)
        self.assertEqual(config.keyword_weight, 0.40)
        
        # More results should be fetched internally
        self.assertEqual(config.semantic_limit, 100)
        self.assertEqual(config.keyword_limit, 100)
    
    def test_score_normalization(self):
        """Test score normalization flag."""
        from kb.library.knowledge_base.hybrid_search import SearchConfig
        
        config = SearchConfig()
        self.assertTrue(config.normalize_scores)


if __name__ == '__main__':
    unittest.main()