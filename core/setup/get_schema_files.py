import os
from pathlib import Path

def get_schema_files(schema_path="schema"):
    """
    Scans the schema directory for .sql files, filters them, 
    and returns a sorted list of full paths.
    """
    # Use Path for better cross-platform support (Linux/Windows)
    base_path = Path(schema_path)

    if not base_path.exists():
        return []

    # Get all .sql files
    files = [
        f for f in base_path.iterdir() 
        if f.is_file() and f.suffix == ".sql" and not f.name.startswith(".")
    ]

    # Sort files by name (ensures 01 runs before 02)
    files.sort(key=lambda x: x.name)

    # Return list of strings (full paths) for compatibility with your existing code
    return [str(f) for f in files]