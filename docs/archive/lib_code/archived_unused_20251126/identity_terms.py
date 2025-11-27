"""
Centralized identity terms for use across the codebase.

This module provides a single source of truth for identity terms to avoid
duplication and ensure consistency across query_engine, index_builder, etc.
"""

# All identity terms that should be excluded from firm name detection
# and used for identity query detection
IDENTITY_TERMS = [
    # Jewish
    'jew', 'jews', 'jewish', 'sephardi', 'sephardim', 'ashkenazi', 'ashkenazim', 
    'court jew', 'court jews', 'kohanim', 'katz',
    
    # Christian denominations
    'quaker', 'quakers', 'huguenot', 'huguenots', 'puritan', 'puritans',
    'catholic', 'catholics', 'mennonite', 'mennonites', 'calvinist', 'presbyterian',
    
    # Muslim
    'muslim', 'muslims', 'islam', 'islamic', 'sunni', 'sunnis', 'shia', 'shiite',
    'alawite', 'druze', 'ismaili', 'maronite', 'maronites',
    
    # Orthodox
    'coptic', 'greek orthodox', 'orthodox', 'old believer', 'old believers',
    
    # Asian religions
    'parsee', 'parsees', 'zoroastrian', 'hindu', 'brahmin', 'brahmins', 'bania', 'banias',
    'dalit', 'dalits', 'caste',
    
    # Ethnic groups
    'greek', 'greeks', 'armenian', 'armenians', 'lebanese', 'syrian', 'syrians',
    'palestinian', 'palestinians', 'basque', 'basques',
    
    # African ethnic groups
    'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',
    
    # Racial
    'black', 'blacks', 'african', 'african american', 'african americans',
    
    # Gender
    'women', 'woman', 'widow', 'widows', 'female',
    
    # LGBTQ+
    'gay', 'gays', 'homosexual', 'homosexuals', 'homosexuality',
    'lesbian', 'lesbians', 'bisexual', 'bisexuals',
    'lgbt', 'lgbtq', 'lgbtq+', 'queer', 'transgender', 'trans',
    'lavender marriage', 'lavender marriages',
    
    # Hispanic/Latino
    'hispanic', 'hispanics', 'latino', 'latina', 'latinx',
    
    # East Asian
    'chinese', 'japanese', 'korean', 'koreans',
    
    # Other
    'templar', 'templars', 'boston brahmin', 'knickerbocker', 'knickerbockers',
]

# Flattened set for fast lookups
IDENTITY_TERMS_SET = set(IDENTITY_TERMS)

def is_identity_term(term: str) -> bool:
    """Check if a term is an identity term."""
    return term.lower() in IDENTITY_TERMS_SET



