#!/usr/bin/env python3
"""
Unified Documentation Builder
Builds MkDocs with mkdocstrings for comprehensive documentation including API reference
"""

import os
import subprocess
from pathlib import Path

def build_unified_docs():
    """Build unified MkDocs site with mkdocstrings API documentation"""
    print("Building unified documentation with mkdocstrings...")

    result = subprocess.run(["mkdocs", "build"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"MkDocs build failed: {result.stderr}")
        return False

    print("SUCCESS: Unified documentation built successfully")
    return True

def serve_docs():
    """Serve the documentation site with live reload"""
    print("Serving documentation with live reload...")
    
    result = subprocess.run(["mkdocs", "serve", "--dev-addr", "localhost:8001"])
    return result.returncode == 0

def main():
    """Main build process"""
    print("Building MLTrading documentation with mkdocstrings...")
    print("=" * 60)

    if not build_unified_docs():
        print("ERROR: Documentation build failed")
        return False

    print("=" * 60)
    print("SUCCESS: Documentation built successfully!")
    print()
    print("Structure:")
    print("  - Guides & Tutorials: Native MkDocs pages")
    print("  - API Reference: Auto-generated from docstrings")
    print("  - All in unified Material Design theme")
    print()
    print("Commands:")
    print("  python build_docs.py serve  # Serve with live reload")
    print("  mkdocs serve               # Alternative serve command")
    print("  mkdocs build               # Build static site")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve_docs()
    else:
        main()