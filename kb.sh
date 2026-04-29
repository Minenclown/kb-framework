#!/bin/bash
# KB Framework CLI Wrapper
# Usage: kb <command> [args]
#
# Uses the virtual environment at KB_DIR/venv/ if available,
# falls back to system python3 otherwise.

# Resolve KB_DIR: env var > self-detection > XDG default
if [ -n "$KB_DIR" ]; then
    # Explicit override via environment
    :
elif [ -n "$BASH_SOURCE" ]; then
    # Self-detection: resolve symlink and find repo root
    SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
    KB_DIR="$(cd "$(dirname "$SELF")" && pwd)"
else
    # Fallback to XDG
    KB_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/kb"
fi

# Resolve symlink if KB_DIR is a symlink
if [ -L "${KB_DIR:-}" ] || [ -d "${KB_DIR:-}" ]; then
    KB_DIR="$(readlink -f "$KB_DIR" 2>/dev/null || echo "$KB_DIR")"
fi

# Determine Python interpreter
if [ -d "$KB_DIR/venv" ]; then
    PYTHON="$KB_DIR/venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

if [ -z "$PYTHON" ]; then
    echo "❌ Python3 is required but not installed"
    exit 1
fi

# Set PYTHONPATH so kb package is findable
export PYTHONPATH="$KB_DIR${PYTHONPATH:+:$PYTHONPATH}"

# Run the Python CLI
exec "$PYTHON" -m kb "$@"