import re

_TAG_RE = re.compile(r"<[^>]+>")

def strip_tags(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return _TAG_RE.sub(" ", text)

POSSESSIVE_PATTERN = re.compile(r"('s|’s)$", re.IGNORECASE)


def canonicalize_term(term: str) -> str:
    """
    Normalize a term so plural/possessive variants map to the same index key.
    - Keeps all-uppercase acronyms (SEC, MMEU) unchanged
    - Converts to lowercase otherwise
    - Strips apostrophes/possessives and trailing 's' for 4+ letter words
    """
    if not term:
        return term
    
    if term.isupper():
        return term
    
    t = term.lower().replace("’", "'").strip("'")
    t = POSSESSIVE_PATTERN.sub('', t)
    t = t.replace("'", "")
    
    if len(t) > 3 and t.endswith('s'):
        t = t[:-1]
    
    return t

