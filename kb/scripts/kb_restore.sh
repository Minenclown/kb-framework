#!/bin/bash
# KB Framework - Restore Script
# Stellt Backups von SQLite DB und ChromaDB wieder her

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/.openclaw/kb/backup}"
KB_DB="${KB_DB:-$HOME/.openclaw/kb/library/biblio.db}"
CHROMA_DB="${CHROMA_DB:-$HOME/.openclaw/kb/.knowledge/chroma_db}"

# Usage
usage() {
    echo "Usage: $0 <backup_name> [--dry-run]"
    echo ""
    echo "Beispiele:"
    echo "  $0 latest                    # Restore from latest backup"
    echo "  $0 kb_backup_20260412_113032  # Restore specific backup"
    echo "  $0 latest --dry-run          # Show what would be restored"
    echo ""
    echo "Um verfügbare Backups zu sehen:"
    echo "  ls ${BACKUP_DIR}"
    exit 1
}

# Args
BACKUP_NAME="${1:-}"
DRY_RUN=false
if [ "$2" = "--dry-run" ]; then
    DRY_RUN=true
fi

# Validate backup name
if [ -z "$BACKUP_NAME" ]; then
    echo "❌ Fehler: Backup-Name erforderlich"
    usage
fi

# Resolve backup path
if [ "$BACKUP_NAME" = "latest" ]; then
    BACKUP_PATH="${BACKUP_DIR}/latest"
else
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
fi

# Check if backup exists
if [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Backup nicht gefunden: ${BACKUP_PATH}"
    echo ""
    echo "Verfügbare Backups:"
    ls -la "${BACKUP_DIR}"/kb_backup_* 2>/dev/null || echo "  Keine Backups gefunden"
    exit 1
fi

echo "🔄 KB Framework Restore"
echo "======================"
echo "Backup: ${BACKUP_PATH}"
echo ""

# Get backup info
if [ -f "${BACKUP_PATH}/metadata.json" ]; then
    echo "📋 Backup Info:"
    cat "${BACKUP_PATH}/metadata.json" | grep -E '"(timestamp|date)"' | head -2
    echo ""
fi

# Verify checksum
verify_checksum() {
    local file="$1"
    local checksum_file="${file}.sha256"
    
    if [ -f "$checksum_file" ]; then
        if sha256sum -c "$checksum_file" > /dev/null 2>&1; then
            echo "  ✅ $file: Prüfsumme OK"
            return 0
        else
            echo "  ❌ $file: Prüfsumme FEHLGESCHLAGEN!"
            return 1
        fi
    else
        echo "  ⚠️  Keine Prüfsumme für $file"
        return 0
    fi
}

# Restore function
restore_sqlite() {
    local backup_sqlite="${BACKUP_PATH}/sqlite/biblio.db"
    
    if [ ! -f "$backup_sqlite" ]; then
        echo "❌ SQLite Backup nicht gefunden: ${backup_sqlite}"
        return 1
    fi
    
    if ! verify_checksum "$backup_sqlite"; then
        echo "❌ Restore abgebrochen wegen Prüfsummenfehler"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] Würde SQLite DB restore: ${backup_sqlite} → ${KB_DB}"
        return 0
    fi
    
    # Create backup of current DB
    if [ -f "$KB_DB" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        cp "$KB_DB" "${KB_DB}.backup_${timestamp}"
        echo "  ✅ Aktuelle DB gesichert: ${KB_DB}.backup_${timestamp}"
    fi
    
    cp "$backup_sqlite" "$KB_DB"
    echo "  ✅ SQLite DB restored: ${KB_DB}"
}

restore_chroma() {
    local backup_chroma="${BACKUP_PATH}/chroma"
    
    if [ ! -d "$backup_chroma" ]; then
        echo "❌ ChromaDB Backup nicht gefunden: ${backup_chroma}"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        echo "  [DRY-RUN] Würde ChromaDB restore: ${backup_chroma} → ${CHROMA_DB}"
        return 0
    fi
    
    # Create backup of current ChromaDB
    if [ -d "$CHROMA_DB" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        rm -rf "${CHROMA_DB}.backup_${timestamp}"
        cp -r "$CHROMA_DB" "${CHROMA_DB}.backup_${timestamp}"
        echo "  ✅ Aktuelle ChromaDB gesichert: ${CHROMA_DB}.backup_${timestamp}"
    fi
    
    rm -rf "$CHROMA_DB"
    cp -r "$backup_chroma" "$CHROMA_DB"
    echo "  ✅ ChromaDB restored: ${CHROMA_DB}"
}

# Perform restore
if [ "$DRY_RUN" = true ]; then
    echo "⚠️  DRY-RUN MODE - Keine Änderungen werden vorgenommen"
    echo ""
fi

echo "📁 SQLite DB..."
restore_sqlite

echo ""
echo "📁 ChromaDB..."
restore_chroma

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "✅ DRY-RUN abgeschlossen (keine Änderungen)"
else
    echo "✅ Restore abgeschlossen!"
    echo ""
    echo "📊 Verify Restore:"
    echo "   SQLite: $(du -h "$KB_DB" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo "   ChromaDB: $(du -sh "$CHROMA_DB" 2>/dev/null | cut -f1 || echo 'N/A')"
fi