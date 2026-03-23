import os
import re

def load_list(file_path):
    """Loads a list from a file, skipping comments and empty lines."""
    if not os.path.exists(file_path): return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def escape_md(text):
    """Escapes special characters for Telegram MarkdownV2."""
    if not text: return ""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))