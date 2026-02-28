import re

def normalize_key(s: str) -> str:
    """
    Normalize names for lookups:
    - lowercase
    - treat hyphens/underscores as spaces
    - collapse whitespace
    - trim
    """
    if s is None:
        return ""
    s = s.strip().lower()
    s = s.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s)
    return s