import re

_TAG_RE = re.compile(r"<[^>]+>")

def strip_tags(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return _TAG_RE.sub(" ", text)

POSSESSIVE_PATTERN = re.compile(r"('s|’s)$", re.IGNORECASE)


def canonicalize_term(term: str) -> str:
    """
    Normalize a term PRESERVING capitalization.
    
    NEW BEHAVIOR:
    - Preserves original capitalization completely (e.g., "Paribas" stays "Paribas", "BANK" stays "BANK")
    - Only removes possessives ('s) - does NOT remove trailing 's' from words
    - This allows distinguishing: "Paribas" (proper noun) vs "bank" (generic word)
    
    Returns:
        Term with possessives removed, capitalization preserved
    """
    if not term:
        return term
    
    # Remove possessives ('s or 's) but preserve everything else
    t = term.replace("'", "'")  # Normalize apostrophes
    t = POSSESSIVE_PATTERN.sub('', t)  # Remove 's
    t = t.replace("'", "")  # Remove any remaining apostrophes
    t = t.strip()
    
    return t

