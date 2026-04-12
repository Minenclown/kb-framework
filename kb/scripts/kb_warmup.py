#!/usr/bin/env python3
"""
KB Warmup – Lädt ChromaDB Model vorab

Laufzeit: Beim Server-Start (via systemd oder OpenClaw init)
Zweck: Erste Query nicht 8s langsam
"""

import sys
sys.path.insert(0, str(Path.home() / ".openclaw" / "kb" / "library"))

from knowledge_base.chroma_integration import ChromaIntegration

def warmup():
    print("Warming up ChromaDB model...")
    chroma = ChromaIntegration()
    
    # Model vorab laden
    _ = chroma.model
    print("Model loaded")
    
    # Collection-Reference holen (initialisiert ChromaDB intern)
    _ = chroma.sections_collection
    print("ChromaDB Collection ready")
    
    print("KB Warmup complete")

if __name__ == "__main__":
    warmup()
