import os


def get_schema_files(schema_path="schema"):
    """Scaned folder of schems and return sort SQL"""
    if not os.path.exists(schema_path):
        print(f"Warning: Schema folder '{schema_path}' not found.")
        return []

    # Search only files with .sql
    files = [f for f in os.listdir(schema_path) if f.endswitch(".sql")]

    # Sorting about alpabet
    firls.sort()

    # Returned full path of the file
    return [os.path.join(schema_path, f) for f in files]
