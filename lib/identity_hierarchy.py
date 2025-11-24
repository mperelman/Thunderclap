"""
Identity Hierarchy - Maps specific identities to general categories for searchability.

Allows both specific searches ("alawite bankers") and general ("muslim bankers").
"""
from typing import List

# Hierarchical mapping: general -> [specific identities]
IDENTITY_HIERARCHY = {
    # Religion hierarchy
    'muslim': ['sunni', 'shia', 'shiite', 'alawite', 'ismaili', 'druze', 'ahmadi', 'sufi'],
    'christian': ['maronite', 'coptic', 'orthodox', 'greek_orthodox', 'melkite', 'nestorian',
                  'catholic', 'protestant', 'anglican', 'presbyterian', 'calvinist',
                  'quaker', 'huguenot', 'mennonite', 'puritan', 'old_believer'],
    'orthodox': ['russian_orthodox', 'greek_orthodox', 'old_believer'],  # Orthodox subdivisions
    'jewish': ['sephardi', 'sephardim', 'ashkenazi', 'ashkenazim', 'mizrahi', 'court_jew',
               'kohanim', 'katz'],
    'hindu': ['brahmin', 'bania', 'kayastha', 'kshatriya', 'vaishya', 'maratha', 
              'dalit', 'untouchable', 'shudra'],  # Added full caste hierarchy
    'buddhist': ['zen', 'theravada', 'mahayana', 'tibetan'],
    
    # Geographic/ethnic hierarchy
    'levantine': ['lebanese', 'syrian', 'palestinian', 'jordanian'],
    'maghrebi': ['moroccan', 'algerian', 'tunisian', 'libyan'],
    'persian': ['iranian', 'persian', 'tajik'],
    'greek': ['greek_orthodox'],  # Greek identity includes Greek Orthodox
    'russian': ['russian_orthodox', 'old_believer', 'belarussian', 'ukrainian'],  # Russian context
    'african': ['nigerian', 'ghanaian', 'kenyan', 'south_african', 'ethiopian',
                'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu', 'xhosa'],
    'latin_american': ['latino', 'hispanic', 'mexican', 'cuban', 'puerto_rican',
                       'colombian', 'venezuelan', 'argentinian', 'chilean', 'brazilian'],
    'arab': ['saudi', 'emirati', 'kuwaiti', 'qatari', 'omani', 'yemeni', 'lebanese', 
             'syrian', 'palestinian', 'jordanian', 'iraqi'],
    'east_asian': ['chinese', 'japanese', 'korean', 'taiwanese', 'hong_kong', 'singaporean',
                   'vietnamese', 'thai', 'filipino', 'indonesian', 'malaysian'],
    
    # Gender/sexual orientation
    'lgbtq': ['gay', 'lesbian', 'bisexual', 'transgender', 'queer', 'lgbt', 'lgbtq'],
    'gender': ['women', 'woman', 'widow', 'widows', 'female', 'feminine'],
    
    # Elite subgroups
    'elite': ['boston_brahmin', 'knickerbocker', 'court_jew', 'patroon', 'royal', 
              'aristocrat', 'patrician'],
    
    # Status
    'religious_status': ['converted', 'converso', 'crypto_jewish', 'marrano'],
}


def get_parent_categories(specific_identity: str) -> List[str]:
    """
    Get all parent categories for a specific identity.
    
    Example:
        get_parent_categories('alawite') -> ['muslim', 'levantine']
        get_parent_categories('maronite') -> ['christian', 'levantine']
    """
    parents = []
    
    for general, specifics in IDENTITY_HIERARCHY.items():
        if specific_identity in specifics:
            parents.append(general)
    
    return parents


def expand_identity_for_search(identity: str) -> List[str]:
    """
    Expand identity term for search - includes both specific and all children.
    
    Example:
        expand_identity_for_search('muslim') -> ['muslim', 'sunni', 'shia', 'alawite', ...]
        expand_identity_for_search('alawite') -> ['alawite'] (no children)
    """
    expanded = [identity]
    
    # If this is a general category, add all children
    if identity in IDENTITY_HIERARCHY:
        expanded.extend(IDENTITY_HIERARCHY[identity])
    
    return expanded


if __name__ == '__main__':
    # Test
    print("Testing hierarchy:")
    print(f"\nParents of 'alawite': {get_parent_categories('alawite')}")
    print(f"Parents of 'maronite': {get_parent_categories('maronite')}")
    print(f"Parents of 'sephardi': {get_parent_categories('sephardi')}")
    
    print(f"\nExpand 'muslim': {expand_identity_for_search('muslim')[:10]}")
    print(f"Expand 'alawite': {expand_identity_for_search('alawite')}")

