import os

def get_schema_files(schema_path="schema"):
    """
    Scans the schema directory for .sql files and returns them sorted.
    """
    if not os.path.exists(schema_path):
        return []

    files = [f for f in os.listdir(schema_path) if f.endswith(".sql")]
    files.sort()
    
    # Return full paths
    return [os.path.join(schema_path, f) for f in files]