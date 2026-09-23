#!/usr/bin/env python3
"""Package SMPF plugins, theme, and backend into ZIP files."""

import os
import zipfile
from pathlib import Path

BASE = Path(r"C:/Users/RudiOosthuizen/smpf")
DEPLOY = BASE / "deploy"
DEPLOY.mkdir(parents=True, exist_ok=True)


def zip_directory(src: Path, dst: Path, exclude=None):
    """Zip a directory, optionally excluding patterns."""
    exclude = exclude or []
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(src):
            root_path = Path(root)
            # Skip __pycache__ dirs
            dirs[:] = [d for d in dirs if d not in exclude]
            for f in files:
                if f.endswith(".pyc"):
                    continue
                file_path = root_path / f
                arcname = file_path.relative_to(src.parent)
                zf.write(file_path, arcname)
    print(f"Created: {dst}")


# ─── Plugins ──────────────────────────────────────────────────────────────
plugins_dir = BASE / "wordpress-plugins"
for plugin_name in ["smpf-core", "smpf-post", "smpf-analytics", "smpf-payments", "smpf-integrations"]:
    src = plugins_dir / plugin_name
    dst = DEPLOY / f"{plugin_name}.zip"
    zip_directory(src, dst, exclude=["__pycache__"])

# ─── Theme ────────────────────────────────────────────────────────────────
theme_dir = BASE / "wordpress-theme"
dst = DEPLOY / "smpf-portal-theme.zip"
zip_directory(theme_dir, dst, exclude=["__pycache__"])

# ─── Backend ──────────────────────────────────────────────────────────────
backend_items = ["main.py", "requirements.txt", "app", "frontend", "data"]
backend_zip = DEPLOY / "smpf-backend-v1.zip"
with zipfile.ZipFile(backend_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    for item in backend_items:
        src = BASE / item
        if src.is_dir():
            for root, dirs, files in os.walk(src):
                root_path = Path(root)
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in files:
                    if f.endswith(".pyc"):
                        continue
                    file_path = root_path / f
                    arcname = file_path.relative_to(BASE)
                    zf.write(file_path, arcname)
        elif src.is_file():
            zf.write(src, src.name)
print(f"Created: {backend_zip}")

# ─── Summary ──────────────────────────────────────────────────────────────
print("\n--- DEPLOY PACKAGE SUMMARY ---")
for f in sorted(DEPLOY.iterdir()):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name:40s} {size_kb:8.1f} KB")
