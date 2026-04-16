"""
KB Knowledge Base Library
=========================

Core components for vector search and knowledge retrieval.

Architecture:
-------------
- ChromaIntegration: Vector DB connection (ChromaDB + sentence-transformers)
- HybridSearch: Unified search combining vector + keyword search
- EmbeddingPipeline: Text embedding with caching
- Reranker: Result scoring and reordering

Modules:
--------
- chroma_integration: ChromaDB connection management
- hybrid_search: Unified search interface
- embedding_pipeline: Text embeddings (all-MiniLM-L6-v2)
- reranker: Result reordering
- chunker: Text segmentation with overlap
- fts5_setup: SQLite FTS5 configuration
- stopwords: German/English stopword lists
- synonyms: Synonym expansion for better recall

Usage:
------
    from kb.knowledge_base import HybridSearch
    
    search = HybridSearch()
    results = search.search("query", limit=5)
"""

# ChromaDB Integration
from .chroma_integration import (
    ChromaIntegration,
    get_chroma,
    embed_text,
    embed_batch,
)

# Hybrid Search
from .hybrid_search import (
    HybridSearch,
    SearchResult,
    SearchConfig,
    get_search,
)

# Embedding Pipeline
from .embedding_pipeline import (
    EmbeddingPipeline,
    SectionRecord,
    EmbeddingJob,
)

# Reranker
from .reranker import (
    Reranker,
    get_reranker,
    rerank,
    RerankResult,
)

# Chunker
from .chunker import (
    Chunk,
    SentenceChunker,
    SimpleChunker,
    chunk_document,
)

# FTS5 Setup
from .fts5_setup import (
    check_fts5_available,
    setup_fts5,
    rebuild_fts5_index,
    get_fts5_stats,
)

# Stopwords
from .stopwords import (
    StopwordHandler,
    get_stopword_handler,
)

# Synonyms
from .synonyms import (
    SynonymExpander,
    get_expander,
    expand_query,
)

# Chroma Plugin
from .chroma_plugin import (
    ChromaDBPlugin,
    EmbeddingTask,
)

# Utils
from .utils import (
    build_embedding_text,
)

# Search Providers (DG-2: Interface-Extraktion)
from .search_providers import (
    SearchResult as ProviderSearchResult,
    SemanticSearchProvider,
    KeywordSearchProvider,
)
from .providers import (
    ChromaSemanticProvider,
    FTS5KeywordProvider,
    get_semantic_provider,
    get_keyword_provider,
)

__all__ = [
    # ChromaDB Integration
    'ChromaIntegration',
    'get_chroma',
    'embed_text',
    'embed_batch',
    # Hybrid Search
    'HybridSearch',
    'SearchResult',
    'SearchConfig',
    'get_search',
    # Embedding Pipeline
    'EmbeddingPipeline',
    'SectionRecord',
    'EmbeddingJob',
    # Reranker
    'Reranker',
    'get_reranker',
    'rerank',
    'RerankResult',
    # Chunker
    'Chunk',
    'SentenceChunker',
    'SimpleChunker',
    'chunk_document',
    # FTS5 Setup
    'check_fts5_available',
    'setup_fts5',
    'rebuild_fts5_index',
    'get_fts5_stats',
    # Stopwords
    'StopwordHandler',
    'get_stopword_handler',
    # Synonyms
    'SynonymExpander',
    'get_expander',
    'expand_query',
    # Chroma Plugin
    'ChromaDBPlugin',
    'EmbeddingTask',
    # Search Providers (DG-2)
    'ProviderSearchResult',
    'SemanticSearchProvider',
    'KeywordSearchProvider',
    'ChromaSemanticProvider',
    'FTS5KeywordProvider',
    'get_semantic_provider',
    'get_keyword_provider',
]