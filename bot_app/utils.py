import re
from typing import List

URL_RE = re.compile(r"https?://[^\s]+")

def extract_urls(text: str) -> List[str]:
    if not text:
        return []
    return URL_RE.findall(text)
