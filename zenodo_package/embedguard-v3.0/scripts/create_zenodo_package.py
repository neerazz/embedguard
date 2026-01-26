#!/usr/bin/env python3
"""
Create Zenodo submission package for EmbedGuard.

This script creates a clean archive suitable for Zenodo upload,
excluding development artifacts like .venv, __pycache__, etc.
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime


def create_zenodo_package():
    """Create a clean Zenodo submission package."""

    # Configuration
    project_root = Path(__file__).parent.parent
    version = "2.1"
    package_name = f"embedguard-v{version}"

    # Output paths
    output_dir = project_root / "zenodo_package"
    package_dir = output_dir / package_name
    zip_path = output_dir / f"{package_name}.zip"

    # Files and directories to include
    include_items = [
        "README.md",
        "ZENODO_README.md",
        "LICENSE",
        "CITATION.cff",
        "requirements.txt",
        "pyproject.toml",
        "DATA_DESCRIPTION.md",
        "SUBMISSION_CHECKLIST.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "src",
        "data",
        "results",
        "examples",
        "tests",
        "paper",
        "scripts",
    ]

    # Patterns to exclude
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".DS_Store",
        ".venv",
        ".git",
        ".gitignore",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        "benchmarks",  # Empty directory
        "models",      # Empty directory
        "experiments", # Development artifacts
    ]

    def should_exclude(path: Path) -> bool:
        """Check if path should be excluded from package."""
        path_str = str(path)
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True
        return False

    def copy_item(src: Path, dst: Path):
        """Copy file or directory, excluding unwanted items."""
        if should_exclude(src):
            return

        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        elif src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for item in src.iterdir():
                copy_item(item, dst / item.name)

    # Clean previous package
    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)
    package_dir.mkdir()

    print(f"Creating Zenodo package: {package_name}")
    print(f"Output directory: {output_dir}")
    print()

    # Copy included items
    for item_name in include_items:
        src_path = project_root / item_name
        dst_path = package_dir / item_name

        if src_path.exists():
            print(f"  Including: {item_name}")
            copy_item(src_path, dst_path)
        else:
            print(f"  Warning: {item_name} not found")

    print()

    # Create ZIP archive
    print(f"Creating ZIP archive: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d)]

            for file in files:
                file_path = Path(root) / file
                if not should_exclude(file_path):
                    arcname = file_path.relative_to(output_dir)
                    zipf.write(file_path, arcname)

    # Calculate archive statistics
    zip_size = zip_path.stat().st_size
    file_count = sum(1 for _ in package_dir.rglob("*") if _.is_file())

    print()
    print("=" * 60)
    print("Zenodo Package Created Successfully!")
    print("=" * 60)
    print(f"  Package: {package_name}")
    print(f"  Location: {zip_path}")
    print(f"  Size: {zip_size / 1024 / 1024:.2f} MB")
    print(f"  Files: {file_count}")
    print(f"  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps for Zenodo submission:")
    print("  1. Go to https://zenodo.org/deposit/new")
    print("  2. Upload the ZIP file")
    print("  3. Fill in metadata (see CITATION.cff)")
    print("  4. Reserve DOI and publish")
    print()

    return zip_path


if __name__ == "__main__":
    create_zenodo_package()
