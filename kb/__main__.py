#!/usr/bin/env python3
"""
KB Framework CLI - Main entry point

Usage:
    python3 -m kb <command> [args]

Commands:
    index <path>        Index a file or directory
    search <query>      Search the knowledge base
    stats               Show KB statistics
    update              Check for and install updates
    audit               Run full audit
    ghost               Find orphaned entries
    warmup              Preload ChromaDB model
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kb.indexer import BiblioIndexer


def cmd_index(args):
    """Index a file or directory."""
    path = Path(args.path)
    if not path.exists():
        print(f"Path not found: {path}")
        return 1

    kb = BiblioIndexer()
    if path.is_file():
        kb.index_file(path)
        print(f"Indexed: {path}")
    else:
        kb.index_directory(path)
        print(f"Indexed directory: {path}")
    return 0


def cmd_search(args):
    """Search the knowledge base."""
    from kb.library.knowledge_base.hybrid_search import HybridSearch

    hs = HybridSearch()
    results = hs.search(args.query, limit=args.limit)

    print(f"Found {len(results)} results for: {args.query}")
    print("-" * 50)

    for r in results[:args.limit]:
        print(f"\n{r.get('file_name', 'Unknown')}")
        print(f"   Score: {r.get('score', 0):.2f}")
        preview = r.get('content_preview', '')[:150]
        if preview:
            print(f"   {preview}...")
    return 0


def cmd_stats(args):
    """Show KB statistics."""
    kb = BiblioIndexer()
    stats = kb.get_stats()

    print("KB Framework Statistics")
    print("=" * 40)
    print(f"Files: {stats.get('files', 'N/A')}")
    print(f"Sections: {stats.get('sections', 'N/A')}")
    print(f"Keywords: {stats.get('keywords', 'N/A')}")
    return 0


def cmd_update(args):
    """Check for updates."""
    from kb import update

    # Pass args to update module
    update.args = args
    update.main()
    return 0


def cmd_audit(args):
    """Run full audit."""
    import subprocess
    script = Path(__file__).parent / "scripts" / "kb_full_audit.py"
    subprocess.run([sys.executable, str(script)])
    return 0


def cmd_ghost(args):
    """Find ghost entries."""
    import subprocess
    script = Path(__file__).parent / "scripts" / "kb_ghost_scanner.py"
    subprocess.run([sys.executable, str(script)])
    return 0


def cmd_warmup(args):
    """Preload ChromaDB model."""
    import subprocess
    script = Path(__file__).parent / "scripts" / "kb_warmup.py"
    subprocess.run([sys.executable, str(script)])
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog='kb',
        description='KB Framework - Knowledge Base Management'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Index command
    p_index = subparsers.add_parser('index', help='Index file or directory')
    p_index.add_argument('path', help='Path to index')

    # Search command
    p_search = subparsers.add_parser('search', help='Search knowledge base')
    p_search.add_argument('query', help='Search query')
    p_search.add_argument('-l', '--limit', type=int, default=10, help='Result limit')

    # Stats command
    p_stats = subparsers.add_parser('stats', help='Show statistics')

    # Update command
    p_update = subparsers.add_parser('update', help='Check for updates')
    p_update.add_argument('--check', action='store_true', help='Only check')
    p_update.add_argument('--force', action='store_true', help='Force update')

    # Audit command
    p_audit = subparsers.add_parser('audit', help='Run full audit')

    # Ghost command
    p_ghost = subparsers.add_parser('ghost', help='Find ghost entries')

    # Warmup command
    p_warmup = subparsers.add_parser('warmup', help='Preload model')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'index': cmd_index,
        'search': cmd_search,
        'stats': cmd_stats,
        'update': cmd_update,
        'audit': cmd_audit,
        'ghost': cmd_ghost,
        'warmup': cmd_warmup,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
