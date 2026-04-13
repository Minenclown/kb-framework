import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'kb'))

from indexer import BiblioIndexer

def test_embeddings_table_exists():
    """Test that embeddings table is created."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    indexer = BiblioIndexer(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
    )
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None, "embeddings table should exist"
    print("✅ embeddings table exists")

def test_embedding_hash():
    """Test SHA256 hash calculation."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    indexer = BiblioIndexer(db_path)
    test_embedding = [0.1] * 384
    hash_result = indexer.get_embedding_hash(test_embedding)
    
    assert len(hash_result) == 64, f"SHA256 hash should be 64 chars, got {len(hash_result)}"
    print("✅ embedding hash calculation works")

if __name__ == '__main__':
    test_embeddings_table_exists()
    test_embedding_hash()
    print("\n✅ All tests passed!")
