"""
Keyword Search Implementations
===============================

FTS5 (BM25) and SQLite LIKE-based keyword search functions.
"""

import sqlite3
import logging
from typing import Optional

from ..fts5_setup import check_fts5_available
from ..text import parse_keywords

# Logging
logger = logging.getLogger(__name__)


def _keyword_search_fts(
    db_conn,
    query: str,
    limit: int = 100,
    keyword_exact_boost: float = 1.5,
    keyword_provider=None,
) -> list[dict]:
    """
    Keyword search — delegates to provider if available, else FTS5/LIKE.

    Uses BM25 (Best Match 25) algorithm for relevance ranking.
    Falls back to LIKE search if FTS5 is not available.

    Args:
        db_conn: SQLite database connection
        query: Query string
        limit: Max results
        keyword_exact_boost: Boost factor for exact keyword matches
        keyword_provider: Optional KeywordSearchProvider (Protocol)

    Returns:
        List of results with keyword match scores
    """
    # DG-2: Use injected provider if available
    if keyword_provider is not None:
        try:
            provider_results = keyword_provider.search(query, limit)
            # Convert SearchResult to dict for compatibility with _merge_and_rank
            return [
                {
                    "section_id": r.section_id,
                    "keyword_score": r.score,
                    "file_id": r.file_id,
                    "file_path": r.file_path,
                    "section_header": r.section_header,
                    "content_preview": r.metadata.get("content_preview", ""),
                    "content_full": r.content,
                    "section_level": 0,
                    "importance_score": r.importance_score,
                    "keywords": r.keywords,
                }
                for r in provider_results
            ]
        except (KeyError, ValueError, AttributeError) as e:
            logger.warning(f"Keyword provider search failed: {e}")
            return []

    # Legacy FTS5/LIKE path
    # Check FTS5 availability (use caller's cached flag)
    if db_conn is None:
        logger.error("No database connection available for keyword search")
        return []

    # Check if FTS5 table exists
    try:
        cursor = db_conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE name='file_sections_fts' AND type='table'"
        )
        if not cursor.fetchone()[0]:
            logger.warning("FTS5 table not found, falling back to LIKE")
            return _keyword_search(db_conn, query, limit, keyword_exact_boost)
    except sqlite3.OperationalError as e:
        logger.warning(f"FTS5 table check failed: {e}, falling back to LIKE")
        return _keyword_search(db_conn, query, limit, keyword_exact_boost)

    # Build FTS5 query - convert simple terms to FTS5 query syntax
    # FTS5 supports AND, OR, NOT operators and prefix matching with *
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]

    if not terms:
        return []

    # Build FTS5 query string
    # Use quoted phrases for multi-word terms, simple terms for single words
    fts5_query_parts = []
    for term in terms:
        if ' ' in term:
            fts5_query_parts.append(f'"{term}"')
        else:
            fts5_query_parts.append(term)

    fts5_query = ' AND '.join(fts5_query_parts)

    try:
        # Execute BM25 query
        # BM25 returns negative values (closer to 0 = better match)
        # We convert to a positive score: higher = better
        sql = """
            SELECT 
                section_id,
                file_id,
                file_path,
                section_header,
                content_preview,
                content_full,
                importance_score,
                keywords,
                bm25(file_sections_fts) as bm25_rank
            FROM file_sections_fts
            WHERE file_sections_fts MATCH ?
            ORDER BY bm25_rank
            LIMIT ?
        """
        cursor = db_conn.execute(sql, (fts5_query, limit))

        results = []
        row_num = 0
        total_rows = cursor.fetchall()  # Get all rows first
        total = len(total_rows)

        for row in total_rows:
            row_num += 1
            section_id, file_id, file_path, section_header, \
            content_preview, content_full, importance_score, \
            keywords_str, bm25_rank = row

            # BM25 rank is negative (closer to 0 = better match)
            # Convert to positive score where higher = better
            #
            # Since BM25 values can be negative or near-zero with low document frequency,
            # we use a combined approach:
            # 1. Position-based score (results are ordered by BM25)
            # 2. BM25 magnitude boost (if significantly negative = better match)

            # Position score: 1.0 for first, decreasing for later results
            position_score = (total - row_num) / total if total > 0 else 0.5

            if bm25_rank is not None and bm25_rank < -0.001:
                # Significant negative BM25 = good match
                # The more negative, the better the match
                # Scale: -0.001 to -10 maps to 0.5 to 1.0
                bm25_boost = min(1.0, max(0.0, 0.5 + abs(bm25_rank) / 20.0))
                # Blend: 70% position, 30% BM25 boost
                bm25_score = 0.7 * position_score + 0.3 * bm25_boost
            else:
                # Near-zero or positive BM25 - rely on position scoring
                bm25_score = position_score

            results.append({
                "section_id": str(section_id),
                "keyword_score": bm25_score,
                "file_id": str(file_id) if file_id else "",
                "file_path": file_path or "",
                "section_header": section_header or "",
                "content_preview": content_preview or "",
                "content_full": content_full or "",
                "section_level": 0,
                "importance_score": importance_score or 0.5,
                "keywords": parse_keywords(keywords_str)
            })

        logger.info(f"FTS5 BM25 search for '{query}': {len(results)} results")
        return results

    except sqlite3.OperationalError as e:
        logger.warning(f"FTS5 BM25 query failed: {e}, falling back to LIKE")
        return _keyword_search(db_conn, query, limit, keyword_exact_boost)


def _keyword_search(
    db_conn,
    query: str,
    limit: int = 100,
    keyword_exact_boost: float = 1.5,
) -> list[dict]:
    """
    Keyword search via SQLite LIKE.

    Args:
        db_conn: SQLite database connection
        query: Query string
        limit: Max results
        keyword_exact_boost: Boost factor for exact keyword matches

    Returns:
        List of results with keyword match scores
    """
    if db_conn is None:
        logger.error("No database connection available for LIKE search")
        return []

    # Build query terms (simple tokenization)
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]

    if not terms:
        return []

    # Build LIKE clauses
    like_clauses = []
    params = []

    for term in terms:
        like_clauses.append("(section_content LIKE ? OR section_header LIKE ?)")
        params.extend([f"%{term}%", f"%{term}%"])

    sql = f"""
        SELECT 
            fs.id, fs.file_id, fs.section_header, fs.section_content, fs.section_level,
            f.file_path
        FROM file_sections fs
        LEFT JOIN files f ON fs.file_id = f.id
        WHERE {' AND '.join(like_clauses)}
        ORDER BY COALESCE(fs.section_level, 0) DESC, fs.id
        LIMIT ?
    """
    params.append(limit)

    cursor = db_conn.execute(sql, params)

    results = []
    for row in cursor.fetchall():
        section_id, file_id, section_header, section_content, section_level, file_path = row
        file_path = file_path or ""

        # Calculate keyword score
        all_text = f"{section_header} {section_content}".lower()
        matches = sum(1 for term in terms if term in all_text)
        keyword_score = matches / len(terms)  # 0.0 to 1.0

        # Exact match bonus
        exact_matches = sum(1 for term in terms if term in all_text.split())
        if exact_matches == len(terms):
            keyword_score *= keyword_exact_boost

        results.append({
            "section_id": str(section_id),
            "keyword_score": min(keyword_score, 1.0),
            "file_id": str(file_id) if file_id else "",
            "file_path": file_path or "",
            "section_header": section_header or "",
            "content_preview": section_content[:500] if section_content else "",
            "content_full": section_content or "",
            "section_level": section_level or 0,
            "importance_score": 0.5,  # Default for file_sections without importance_score
            "keywords": []
        })

    return results