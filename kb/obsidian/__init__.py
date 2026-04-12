"""
Obsidian Integration Module for KB Framework.

Parses Obsidian vault files: WikiLinks, Tags, Frontmatter, Embeds.
Resolves wiki links to file paths using shortest-match algorithm.
"""

from kb.obsidian.parser import (
    WIKILINK_PATTERN,
    EMBED_PATTERN,
    TAG_PATTERN,
    FRONTMATTER_PATTERN,
    parse_frontmatter,
    extract_wikilinks,
    extract_tags,
    extract_embeds,
)

from kb.obsidian.resolver import (
    PathResolver,
    resolve_wikilink,
)

from kb.obsidian.writer import (
    VaultWriter,
    create_note,
    update_frontmatter,
)

__all__ = [
    # Parser
    'WIKILINK_PATTERN',
    'EMBED_PATTERN',
    'TAG_PATTERN',
    'FRONTMATTER_PATTERN',
    'parse_frontmatter',
    'extract_wikilinks',
    'extract_tags',
    'extract_embeds',
    # Resolver
    'PathResolver',
    'resolve_wikilink',
    # Writer
    'VaultWriter',
    'create_note',
    'update_frontmatter',
]
