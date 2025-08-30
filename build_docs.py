#!/usr/bin/env python3
"""
Unified Documentation Builder
Builds both MkDocs (guides) and Sphinx (API) documentation and combines them into one site
"""

import os
import shutil
import subprocess
from pathlib import Path


def build_sphinx_docs():
    """Build Sphinx API documentation"""
    print("Building Sphinx API documentation...")

    # Build Sphinx docs
    sphinx_dir = Path("api-docs")
    result = subprocess.run([
        "sphinx-build", "-b", "html",
        str(sphinx_dir),
        str(sphinx_dir / "_build" / "html")
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Sphinx build failed: {result.stderr}")
        return False

    print("SUCCESS: Sphinx API docs built successfully")
    return True


def build_mkdocs():
    """Build MkDocs site"""
    print("Building MkDocs site...")

    result = subprocess.run(["mkdocs", "build"], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"MkDocs build failed: {result.stderr}")
        return False

    print("SUCCESS: MkDocs site built successfully")
    return True


def combine_sites():
    """Combine Sphinx and MkDocs into unified site"""
    print("Combining documentation sites...")

    # Copy Sphinx HTML output to MkDocs site/api/ directory
    sphinx_html = Path("api-docs/_build/html")
    mkdocs_site = Path("site")
    api_destination = mkdocs_site / "api-docs"

    if not sphinx_html.exists():
        print("❌ Sphinx HTML output not found")
        return False

    if not mkdocs_site.exists():
        print("❌ MkDocs site output not found")
        return False

    # Remove existing API docs if they exist
    if api_destination.exists():
        shutil.rmtree(api_destination)

    # Copy Sphinx output to MkDocs site
    shutil.copytree(sphinx_html, api_destination)

    # Create redirect page in MkDocs API section
    api_index = mkdocs_site / "api" / "index.html"
    api_index.parent.mkdir(exist_ok=True)

    with open(api_index, "w") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Redirecting to API Documentation</title>
    <meta http-equiv="refresh" content="0; url=../api-docs/index.html">
    <script>
        window.location.href = "../api-docs/index.html";
    </script>
</head>
<body>
    <p>Redirecting to <a href="../api-docs/index.html">API Documentation</a>...</p>
</body>
</html>
        """.strip())

    print("SUCCESS: Documentation sites combined successfully")
    print(f"Unified site available at: {mkdocs_site.absolute()}")
    return True


def serve_unified_docs():
    """Serve the unified documentation site"""
    print("Serving unified documentation...")

    site_dir = Path("site")
    if not site_dir.exists():
        print("❌ Site directory not found. Run build first.")
        return False

    # Simple HTTP server
    import http.server
    import socketserver
    import webbrowser

    os.chdir(site_dir)
    PORT = 8001

    try:
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"Serving unified docs at http://localhost:{PORT}")
            print("MkDocs: Main site")
            print("Sphinx API: /api-docs/")
            print("Press Ctrl+C to stop")

            # Open browser
            webbrowser.open(f"http://localhost:{PORT}")

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDocumentation server stopped")


def main():
    """Main build process"""
    print("Building unified MLTrading documentation...")
    print("=" * 50)

    # Build both documentation systems
    sphinx_success = build_sphinx_docs()
    mkdocs_success = build_mkdocs()

    if not (sphinx_success and mkdocs_success):
        print("❌ Documentation build failed")
        return False

    # Combine into unified site
    if not combine_sites():
        print("❌ Failed to combine documentation sites")
        return False

    print("=" * 50)
    print("SUCCESS: Unified documentation built successfully!")
    print()
    print("MkDocs (guides, tutorials): docs/ -> site/")
    print("Sphinx (API reference): api-docs/ -> site/api-docs/")
    print()
    print("Commands:")
    print("  python build_docs.py serve  # Serve unified site")
    print("  mkdocs serve                # Serve MkDocs only")
    print("  cd api-docs && sphinx-build -b html . _build/html  # Build API docs")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve_unified_docs()
    else:
        main()
