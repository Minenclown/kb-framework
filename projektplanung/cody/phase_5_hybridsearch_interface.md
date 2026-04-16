# Phase 5: HybridSearch Interface (DG-2 Option A) - GRÖSSTES PROJEKT

## Context
HybridSearch ist eng gekoppelt mit ChromaDB und SQLite FTS5.
DG-2 Entscheidung: Interface-Extraktion für Cluster-Analyse ohne ChromaDB.

**Aufwand: ~2 Tage (8 Stunden)**

## Ziel-Architektur
```
                    ┌─────────────────────┐
                    │   SearchProvider    │
                    │     (Protocol)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
    ┌─────────▼─────────┐           ┌─────────▼─────────┐
    │ SemanticSearch     │           │ KeywordSearch     │
    │   Provider         │           │   Provider        │
    │   (ABC)            │           │   (ABC)           │
    └─────────┬─────────┘           └─────────┬─────────┘
              │                                 │
     ┌────────▼────────┐              ┌────────▼────────┐
     │ChromaSemantic   │              │SQLiteFTS5       │
     │  Provider       │              │  Provider       │
     └─────────────────┘              └─────────────────┘

              ┌──────────────────────────┐
              │      HybridSearch        │
              │  (uses injected providers)│
              └──────────────────────────┘
```

## Files
### Neu zu erstellen:
- `src/library/search_providers.py` - Interfaces/Protocols
- `src/library/providers/chroma_provider.py` - ChromaDB Implementation
- `src/library/providers/fts5_provider.py` - SQLite FTS5 Implementation

### Zu ändern:
- `src/library/hybrid_search.py` - Refactor für Provider Injection

## Phases

### Phase 5a: Interface definieren (4h)

#### 1. search_providers.py erstellen
```python
"""Search Provider Interfaces für KB Framework"""
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass
class SearchResult:
    content: str
    score: float
    metadata: dict

@runtime_checkable
class SemanticSearchProvider(Protocol):
    """Interface for semantic/vector search"""
    
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        """Search using embeddings/vectors"""
        ...

@runtime_checkable
class KeywordSearchProvider(Protocol):
    """Interface for keyword/BM25 search"""
    
    @abstractmethod
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        """Search using keyword matching"""
        ...
```

### Phase 5b: ChromaDB Provider (4h)

#### 2. ChromaSemanticProvider
```python
"""ChromaDB-backed Semantic Search Provider"""
from typing import list
from src.library.search_providers import SemanticSearchProvider, SearchResult

class ChromaSemanticProvider:
    """Wraps ChromaIntegration for SemanticSearchProvider interface"""
    
    def __init__(self, collection_name: str = "kb_embeddings"):
        self.collection_name = collection_name
        # Existing ChromaIntegration nutzen
    
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        # Delegieren an ChromaIntegration
        results = await self.chroma.search(query, limit)
        return [SearchResult(content=r['content'], 
                            score=r['distance'],
                            metadata=r['metadata']) 
                for r in results]
```

#### 3. FTS5 Keyword Provider
```python
"""SQLite FTS5-backed Keyword Search Provider"""
from typing import list
from src.library.search_providers import KeywordSearchProvider, SearchResult

class FTS5KeywordProvider:
    """Wraps SQLite FTS5 for KeywordSearchProvider interface"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
    
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        # Bestehende FTS5-Suche nutzen
        results = await self._fts5_search(query, limit)
        return [SearchResult(content=r['content'],
                            score=r['rank'],
                            metadata=r['metadata'])
                for r in results]
```

### Phase 5c: HybridSearch refaktorieren (4h)

#### 4. HybridSearch mit Provider Injection
```python
class HybridSearch:
    """Unified search with semantic + keyword providers"""
    
    def __init__(self, 
                 semantic_provider: SemanticSearchProvider | None = None,
                 keyword_provider: KeywordSearchProvider | None = None):
        self.semantic = semantic_provider
        self.keyword = keyword_provider
    
    async def search(self, query: str, limit: int = 10, 
                    mode: str = "hybrid") -> list[SearchResult]:
        """Search using configured providers"""
        results = []
        
        if mode in ("semantic", "hybrid") and self.semantic:
            sem_results = await self.semantic.search(query, limit)
            results.extend(sem_results)
        
        if mode in ("keyword", "hybrid") and self.keyword:
            kw_results = await self.keyword.search(query, limit)
            results.extend(kw_results)
        
        # Merge and rerank
        return self._merge_results(results, limit)
```

### Phase 5d: Cluster-Modus ohne ChromaDB (4h)

#### 5. Fallback für Cluster ohne ChromaDB
```python
class TFIDFSemanticProvider:
    """Simple TF-IDF based semantic search (no ChromaDB needed)"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Load existing embeddings from SQLite
    
    async def search(self, query: str, limit: int) -> list[SearchResult]:
        # Compute query embedding using same model
        # Cosine similarity against stored embeddings
        # Return top-k results
```

### Phase 5e: Provider Registry
```python
# src/library/providers/__init__.py
from .chroma_provider import ChromaSemanticProvider
from .fts5_provider import FTS5KeywordProvider

def get_provider(provider_type: str, **kwargs):
    """Factory für Search Providers"""
    providers = {
        'chroma': ChromaSemanticProvider,
        'fts5': FTS5KeywordProvider,
        'tfidf': TFIDFSemanticProvider,
    }
    return providers[provider_type](**kwargs)
```

## Verification
```bash
# Interface compliance test
python -c "
from src.library.search_providers import SearchResult, SemanticSearchProvider, KeywordSearchProvider

# ChromaProvider implementiert SemanticSearchProvider
from src.library.providers.chroma_provider import ChromaSemanticProvider
provider = ChromaSemanticProvider()
assert isinstance(provider, SemanticSearchProvider)

# FTS5Provider implementiert KeywordSearchProvider
from src.library.providers.fts5_provider import FTS5KeywordProvider
fts5 = FTS5KeywordProvider(db_path=Path('test.db'))
assert isinstance(fts5, KeywordSearchProvider)
"

# Cluster mode without ChromaDB
python -c "
from src.library.hybrid_search import HybridSearch
from src.library.providers.fts5_provider import FTS5KeywordProvider

# Without ChromaDB - only keyword search
hs = HybridSearch(semantic_provider=None, keyword_provider=FTS5KeywordProvider())
results = await hs.search('test', limit=10)
print(f'Got {len(results)} results')
"
```

## Rollback
```bash
cd ~/projects/kb-framework && git checkout src/library/hybrid_search.py
# Remove new provider files if they break things
rm -f src/library/search_providers.py
rm -f src/library/providers/chroma_provider.py
rm -f src/library/providers/fts5_provider.py
rmdir src/library/providers 2>/dev/null || true
```

## Timeout
2 Tage (8 Stunden) - GRÖSSTES PROJEKT

## Risks
- Breaking changes für bestehende HybridSearch-Nutzer
- ChromaDB Connection handling muss erhalten bleiben
- Performance: Provider injection overhead