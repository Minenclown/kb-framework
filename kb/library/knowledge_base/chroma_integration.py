"""
ChromaDB Integration für Lumens Knowledge Base
===============================================

Phase 1: Vector Search Foundation
Lokale ChromaDB Instance mit SQLite als Primary Store.

Embedding-Modell: sentence-transformers/all-MiniLM-L6-v2
Dimensionality: 384

Quelle: KB_Erweiterungs_Plan.md (Phase 1)
"""

import chromadb
from chromadb.config import Settings
from chromadb.errors import NotFoundError as ChromaNotFoundError
from pathlib import Path
import logging
from typing import Optional
from contextlib import contextmanager

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from kb.config import CHROMA_PATH as _default_chroma_path
except ImportError:
    _default_chroma_path = "library/chroma_db/"

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaIntegration:
    """
    ChromaDB Wrapper für Knowledge Base Integration.
    
    Responsibility:
    - Connection Management zu ChromaDB
    - Collection Creation/Retrieval
    - Embedding-Funktion (all-MiniLM-L6-v2)
    """
    
    # Singleton instance
    _instance: Optional['ChromaIntegration'] = None
    
    def __init__(
        self, 
        chroma_path: str = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize ChromaDB Connection.
        
        Args:
            chroma_path: Pfad für persistente ChromaDB Instance
            model_name: Embedding-Modell (Hugging Face model name)
        """
        if chroma_path is None:
            self.chroma_path = Path(_default_chroma_path)
        else:
            self.chroma_path = Path(chroma_path).expanduser()
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self._model = None
        self._client = None
        
        logger.info(f"ChromaIntegration init: path={self.chroma_path}, model={model_name}")
    
    @property
    def client(self) -> chromadb.PersistentClient:
        """Lazy-load ChromaDB Client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.chroma_path),
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB Client initialized")
        return self._client
    
    @property
    def model(self):
        """Lazy-load Sentence Transformer Model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Sentence Transformer loaded: {self.model_name}")
        return self._model
    
    def embed_text(self, text: str) -> list[float]:
        """
        Konvertiert Text zu Vektor-Embedding.
        
        Args:
            text: Input-Text
            
        Returns:
            Normalisierter Embedding-Vektor (384 dimension)
        """
        if not text or not text.strip():
            return [0.0] * 384
        return self.model.encode(
            text, 
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        Batch-Embedding für mehrere Texte.
        
        Args:
            texts: Liste von Texten
            batch_size: Batch-Größe für Inference
            
        Returns:
            Liste von Embedding-Vektoren
        """
        if not texts:
            return []
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=True
        ).tolist()
    
    # -------------------------------------------------------------------------
    # Collection Management
    # -------------------------------------------------------------------------
    
    def get_or_create_collection(
        self, 
        name: str, 
        metadata: Optional[dict] = None
    ) -> chromadb.Collection:
        """
        Erstellt oder holt eine Collection.
        
        Args:
            name: Collection-Name
            metadata: Optionale Metadaten
            
        Returns:
            ChromaDB Collection
        """
        try:
            collection = self.client.get_collection(name=name)
            logger.info(f"Collection retrieved: {name}")
        except ChromaNotFoundError:
            collection = self.client.create_collection(
                name=name,
                metadata=metadata or {"description": f"Collection: {name}"}
            )
            logger.info(f"Collection created: {name}")
        
        return collection
    
    def delete_collection(self, name: str) -> bool:
        """
        Löscht eine Collection.
        
        Args:
            name: Collection-Name
            
        Returns:
            True wenn gelöscht
        """
        try:
            self.client.delete_collection(name=name)
            logger.info(f"Collection deleted: {name}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete collection {name}: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # Pre-configured Collections
    # -------------------------------------------------------------------------
    
    @property
    def sections_collection(self) -> chromadb.Collection:
        """Collection für file_sections Embeddings."""
        return self.get_or_create_collection(
            name="kb_sections",
            metadata={
                "description": "Knowledge Base Sections Embeddings",
                "embedding_model": self.model_name,
                "dimension": 384
            }
        )
    
    @property
    def entities_collection(self) -> chromadb.Collection:
        """Collection für Knowledge Graph Entities."""
        return self.get_or_create_collection(
            name="kg_entities",
            metadata={
                "description": "Knowledge Graph Entities Embeddings",
                "embedding_model": self.model_name,
                "dimension": 384
            }
        )
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def get_collection_stats(self, collection_name: str) -> dict:
        """Holt Statistiken für eine Collection."""
        collection = self.client.get_collection(collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    
    def delete_by_file_id(self, file_id: str, collection_name: str = "kb_sections") -> int:
        """
        Löscht alle Embeddings für eine file_id aus ChromaDB.
        
        ChromaDB unterstützt kein DELETE mit WHERE - daher:
        1. Query alle IDs mit passender file_id via Metadaten
        2. Lösche via delete_by_ids()
        
        Args:
            file_id: UUID der Datei
            collection_name: ChromaDB Collection Name
            
        Returns:
            Anzahl der gelöschten Einträge
        """
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Query alle IDs mit passender file_id in Metadaten
            results = collection.get(where={"file_id": file_id})
            
            if not results or not results.get('ids'):
                logger.debug(f"No ChromaDB entries found for file_id: {file_id}")
                return 0
            
            ids_to_delete = results['ids']
            collection.delete(ids=ids_to_delete)
            
            logger.info(f"Deleted {len(ids_to_delete)} entries from ChromaDB for file_id: {file_id}")
            return len(ids_to_delete)
            
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB for file_id {file_id}: {e}")
            return 0
    
    def list_collections(self) -> list[dict]:
        """Liste aller Collections mit Statistiken."""
        collections = self.client.list_collections()
        return [
            {
                "name": c.name,
                "count": c.count(),
                "metadata": c.metadata
            }
            for c in collections
        ]
    
    def reset_all(self) -> None:
        """Reset aller Collections (gefährlich!)."""
        self.client.reset()
        logger.warning("All ChromaDB collections reset!")
    
    # -------------------------------------------------------------------------
    # Singleton Access
    # -------------------------------------------------------------------------
    
    @classmethod
    def get_instance(cls, **kwargs) -> 'ChromaIntegration':
        """Singleton-Pattern für Connection-Sharing."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset Singleton (für Tests)."""
        cls._instance = None


# =============================================================================
# Convenience Functions (Module-Level API)
# =============================================================================

# Lazy-initialized global instance
_global_instance: Optional[ChromaIntegration] = None

def get_chroma(**kwargs) -> ChromaIntegration:
    """Holt oder erstellt globale ChromaIntegration Instance."""
    global _global_instance
    if _global_instance is None:
        _global_instance = ChromaIntegration.get_instance(**kwargs)
    return _global_instance

def embed_text(text: str) -> list[float]:
    """Convenience: Single text embedding."""
    return get_chroma().embed_text(text)

def embed_batch(texts: list[str], **kwargs) -> list[list[float]]:
    """Convenience: Batch text embedding."""
    return get_chroma().embed_batch(texts, **kwargs)


# =============================================================================
# Main: Quick Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ChromaDB Integration - Quick Test")
    print("=" * 60)
    
    chroma = ChromaIntegration()
    
    # Test embedding
    test_texts = [
        "MTHFR Genmutation C677T Behandlung mit 5-MTHF",
        "BSV Blockchain Semantic Verification für KI-Agenten",
        "LDL Cholesterin Zielwert unter 100 mg/dL"
    ]
    
    print("\n[1] Testing Embedding...")
    embeddings = chroma.embed_batch(test_texts)
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Dimension: {len(embeddings[0]) if embeddings else 0}")
    
    print("\n[2] Testing Collection Management...")
    collection = chroma.sections_collection
    print(f"   Collection: {collection.name}")
    print(f"   Count: {collection.count()}")
    
    print("\n[3] Listing Collections...")
    for col in chroma.list_collections():
        print(f"   - {col['name']}: {col['count']} items")
    
    print("\n[4] Testing Query (semantic search)...")
    test_query = "Genetische Behandlung Methylierung"
    query_emb = chroma.embed_text(test_query)
    
    # Add some test data first
    test_ids = ["test1", "test2", "test3"]
    test_metadatas = [
        {"source": "gesundheit", "type": "fact"},
        {"source": "projekte", "type": "fact"},
        {"source": "gesundheit", "type": "advice"}
    ]
    
    collection.upsert(
        ids=test_ids,
        embeddings=embeddings,
        metadatas=test_metadatas,
        documents=test_texts
    )
    print(f"   Upserted {len(test_ids)} test documents")
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=3
    )
    print(f"   Query: '{test_query}'")
    print(f"   Results: {len(results['ids'][0])} matches")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
