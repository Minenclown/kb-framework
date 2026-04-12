#!/bin/bash
# KB Framework - Quick Install

set -e

echo "🔧 KB Framework Installation..."

# 1. Create directories
mkdir -p ~/.knowledge/chroma_db/
mkdir -p ~/.knowledge/backup/

echo "📦 Installiere System-Dependencies (Tesseract OCR)..."
# Tesseract OCR für PDF-Indexierung
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng 2>/dev/null || \
    apt-get install -y tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng 2>/dev/null || \
    echo "⚠️  Tesseract installation skipped (no sudo)"
fi

echo "📦 Installiere Python-Dependencies..."
pip install chromadb --quiet
pip install sentence-transformers --quiet
pip install pypdf --quiet

echo "📦 Installiere EasyOCR (optional, für bildbasierte PDFs)..."
pip install easyocr torch --quiet 2>/dev/null || echo "⚠️  EasyOCR installation failed (optional)"

echo "📦 Installiere PyMuPDF (für PDF-zu-Bild Konvertierung)..."
pip install pymupdf --quiet 2>/dev/null || echo "⚠️  PyMuPDF installation failed"

# 2. Copy to OpenClaw workspace (if exists)
if [ -d ~/.openclaw/workspace ]; then
    cp -r kb_framework ~/.openclaw/workspace/ 2>/dev/null || true
    echo "✅ Kopiert nach ~/.openclaw/workspace/kb_framework/"
fi

# 3. Create sample config
if [ ! -f kb_framework/kb/config.py ] && [ -f kb_framework/kb/config.py.template ]; then
    cp kb_framework/kb/config.py.template kb_framework/kb/config.py
    echo "✅ config.py erstellt (bitte anpassen!)"
fi

echo ""
echo "✅ KB Framework installiert!"
echo ""
echo "Tesseract Status:"
tesseract --version 2>/dev/null | head -1 || echo "  ⚠️  Nicht installiert"
echo ""
echo "Nächste Schritte:"
echo "  1. Datenbank initialisieren:"
echo "     python3 kb_framework/kb/indexer.py"
echo "  2. Backup erstellen:"
echo "     bash kb_framework/kb/scripts/kb_backup.sh"
echo "  3. Embeddings generieren:"
echo "     python3 kb_framework/kb/library/knowledge_base/embedding_pipeline.py --stats"
echo ""
