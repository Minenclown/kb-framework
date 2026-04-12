#!/bin/bash
# KB Framework - Backup Script
# Erstellt Backups von SQLite DB und ChromaDB

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/knowledge/backup}"
KB_DB="${KB_DB:-$HOME/knowledge/knowledge.db}"
CHROMA_DB="${CHROMA_DB:-$HOME/.knowledge/chroma_db}"

# Konfiguration
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="kb_backup_${TIMESTAMP}"

echo "📦 KB Framework Backup"
echo "====================="
echo "Backup-Verzeichnis: ${BACKUP_DIR}"
echo "Retention: ${RETENTION_DAYS} Tage"
echo ""

# Backup-Verzeichnis erstellen
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# Funktion für Backup mit Prüfsumme
backup_file() {
    local source="$1"
    local dest="$2"
    local name=$(basename "$source")
    
    if [ -f "$source" ]; then
        cp "$source" "$dest/$name"
        sha256sum "$dest/$name" > "$dest/${name}.sha256"
        echo "  ✅ $name ($(du -h "$source" | cut -f1))"
    else
        echo "  ⚠️  Nicht gefunden: $source"
    fi
}

# SQLite DB backup
echo "📁 SQLite DB..."
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/sqlite"
backup_file "$KB_DB" "${BACKUP_DIR}/${BACKUP_NAME}/sqlite"

# ChromaDB backup
echo "📁 ChromaDB..."
if [ -d "$CHROMA_DB" ]; then
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}/chroma"
    cp -r "$CHROMA_DB"/* "${BACKUP_DIR}/${BACKUP_NAME}/chroma/" 2>/dev/null || true
    echo "  ✅ chroma_db/ ($(du -sh "$CHROMA_DB" | cut -f1))"
else
    echo "  ⚠️  ChromaDB nicht gefunden: $CHROMA_DB"
fi

# Metadata JSON
echo "📁 Metadata..."
cat > "${BACKUP_DIR}/${BACKUP_NAME}/metadata.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "sqlite_db": "$(du -h "$KB_DB" 2>/dev/null | cut -f1 || echo 'N/A')}",
    "chroma_db": "$(du -sh "$CHROMA_DB" 2>/dev/null | cut -f1 || echo 'N/A')}",
    "retention_days": ${RETENTION_DAYS}
}
EOF
echo "  ✅ metadata.json"

# Alte Backups aufräumen
echo ""
echo "🧹 Aufräumen (Retention: ${RETENTION_DAYS} Tage)..."
find "${BACKUP_DIR}" -maxdepth 1 -type d -name "kb_backup_*" -mtime +${RETENTION_DAYS} -exec rm -rf {} \; 2>/dev/null || true
OLD_COUNT=$(find "${BACKUP_DIR}" -maxdepth 1 -type d -name "kb_backup_*" 2>/dev/null | wc -l)
echo "  ✅ ${OLD_COUNT} Backups verblieben"

# Zusammenfassung
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" 2>/dev/null | cut -f1)
echo ""
echo "✅ Backup erstellt: ${BACKUP_NAME}"
echo "   Größe: ${BACKUP_SIZE}"
echo "   Pfad: ${BACKUP_DIR}/${BACKUP_NAME}/"

# Symlink auf aktuelles Backup
ln -sf "${BACKUP_DIR}/${BACKUP_NAME}" "${BACKUP_DIR}/latest"
echo "   Symlink: ${BACKUP_DIR}/latest"