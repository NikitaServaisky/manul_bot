import os
import re
import urllib.parse


def create_facebook_deep_link(post_text):
    encoded_text = urllib.parse.quote(post_text)
    return f"https://www.facebook.com/sharer/sharer.php?u=https://facebook.com/MANUL_GARAGE&quote={encoded_text}"


def load_list(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def escape_md(text):
    if not text:
        return ""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", str(text))
