"""
Cousinhood Detector - Learns banking family patterns from documents.
Extracts identity-family relationships and clusters them into cousinhoods.
"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class CousinoodDetector:
    """Detects banking cousinhoods from document text."""
    
    def __init__(self):
        self.identity_families = defaultdict(lambda: defaultdict(int))  # identity -> family -> count
        self.family_cooccurrence = defaultdict(lambda: defaultdict(int))  # family -> family -> count
        self.family_geography = defaultdict(lambda: defaultdict(int))  # family -> geography -> count
        self.family_ancestry = {}  # family -> {origin_family, origin_identity}
        self.explicit_identities = defaultdict(set)  # family -> set of identities explicitly stated
    
    def extract_from_documents(self, chunks: List[str]) -> Dict:
        """
        Extract cousinhood patterns from document chunks.
        
        Args:
            chunks: List of document text chunks
        
        Returns:
            Dictionary with detected patterns
        """
        print("Detecting cousinhood patterns from documents...")
        
        # Identity terms to search for
        identities = [
            'jew', 'jews', 'jewish',
            'quaker', 'quakers',
            'huguenot', 'huguenots',
            'mennonite', 'mennonites',
            'calvinist', 'calvinists',
            'presbyterian', 'presbyterians',
            'parsee', 'parsees', 'parsi',
            'hindu', 'hindus',
            'brahmin', 'brahmins',
            'bania', 'banias',
            'armenian', 'armenians',
            'greek', 'greeks',
            'puritan', 'puritans',
            'sephardim', 'sephardi', 'sephardic',
            'ashkenazim', 'ashkenazi', 'ashkenazic',
            'court jew', 'court jews',
            'boston brahmin', 'boston brahmins',
            'catholic irish', 'irish catholic',
            'overseas chinese', 'sino-thai', 'chinese thai',
            'chaebol', 'chaebols',
            'zaibatsu'
        ]
        
        # Noise words to exclude (generic terms, not family names)
        self.noise_words = {
            # Identity terms themselves
            'jew', 'jews', 'jewish', 'quaker', 'quakers', 'huguenot', 'huguenots',
            'parsee', 'parsees', 'hindu', 'hindus', 'brahmin', 'brahmins',
            'armenian', 'armenians', 'greek', 'greeks', 'puritan', 'puritans',
            'sephardi', 'sephardim', 'ashkenazi', 'ashkenazim', 'mennonite', 'mennonites',
            'calvinist', 'calvinists', 'presbyterian', 'presbyterians',
            'overseas', 'chinese', 'chaebol', 'chaebols', 'zaibatsu',
            'bania', 'banias', 'maratha', 'marathas',
            # Business terms
            'bank', 'banks', 'banker', 'bankers', 'banking',
            'company', 'companies', 'firm', 'firms', 'house', 'houses',
            'merchant', 'merchants', 'trader', 'traders', 'trading',
            'partner', 'partners', 'partnership', 'agent', 'agents',
            'court', 'rabbi', 'protestant', 'catholic',
            # Social/family terms
            'family', 'families', 'community', 'communities', 'group', 'groups',
            'people', 'person', 'member', 'members', 'elite', 'elites',
            'network', 'networks', 'circle', 'circles', 'society',
            # Common action words/verbs that get capitalized
            'also', 'were', 'continued', 'converted', 'became', 'made',
            'while', 'after', 'likewise', 'before', 'later', 'early',
            'played', 'moved', 'married', 'grew', 'fled', 'faced', 'lived',
            'thrived', 'dominated', 'kinterlinked', 'descended', 'trade',
            'like', 'within', 'outside', 'against', 'rights', 'businesses',
            'directors', 'leaders', 'marriages', 'heritage', 'interests',
            'grandfather', 'descendant', 'descendants', 'immigrants',
            'cousins', 'cousin', 'nephew', 'uncle', 'ancestor', 'ancestors',
            'engineering', 'interests', 'metropolis', 'played',
            # More common words/concepts
            'caste', 'influence', 'expelled', 'population', 'accounted',
            'emancipation', 'involved', 'left', 'lead', 'allowed', 'flee',
            'established', 'connected', 'faith', 'remained', 'soon', 'there',
            'wealth', 'ownership', 'enter', 'jean', 'church', 'expelled',
            'power', 'control', 'access', 'capital', 'credit', 'commerce',
            # Geographic terms (cities, countries, regions)
            'america', 'york', 'london', 'paris', 'boston', 'india', 'britain',
            'france', 'germany', 'holland', 'ottoman', 'bengal', 'philadelphia',
            'vienna', 'berlin', 'cologne', 'hamburg', 'amsterdam', 'constantinople',
            'spain', 'austria', 'russia', 'poland', 'hungary', 'prussia',
            'china', 'canton', 'bombay', 'calcutta', 'bengal', 'burma',
            'africa', 'algeria', 'albania', 'algiers', 'alsace', 'atlanta',
            'angola', 'arabia', 'arabs', 'arizona', 'arkansas', 'atlanta',
            'morocco', 'bavaria', 'bohemia', 'galicia', 'moravia', 'silesia',
            'saxony', 'westphalia', 'rhineland', 'swabia', 'franconia',
            # National/ethnic adjectives
            'turkish', 'french', 'german', 'english', 'dutch', 'russian', 'italian',
            'spanish', 'portuguese', 'chinese', 'japanese', 'african',
            'austrian', 'austro', 'american', 'anglo', 'bavarian', 'belgian',
            # Common words that appear capitalized
            'this', 'that', 'their', 'these', 'those', 'with', 'from', 'into',
            'although', 'among', 'amidst', 'another', 'after', 'along',
            'since', 'however', 'along', 'over', 'under', 'until', 'during',
            'while', 'where', 'when', 'which', 'about', 'above', 'across',
            # Titles and political terms
            'parliament', 'congress', 'assembly', 'senate', 'council',
            'king', 'queen', 'prince', 'princess', 'emperor', 'duke',
            'president', 'general', 'minister', 'chancellor',
            # Common first names
            'charles', 'george', 'william', 'henry', 'john', 'james',
            'robert', 'david', 'thomas', 'joseph', 'edward', 'richard',
            'michael', 'daniel', 'samuel', 'alexander', 'benjamin',
            # Regional identifiers
            'scots', 'irish', 'welsh', 'english', 'french', 'german',
            'scottish', 'british', 'european', 'asian', 'middle',
            # Institutions
            'harvard', 'yale', 'oxford', 'cambridge',
            'microsoft', 'google', 'facebook', 'apple',
            # Time/measurement terms
            'years', 'century', 'decades', 'period', 'times', 'months',
            # Generic descriptors
            'many', 'some', 'several', 'various', 'other', 'others',
            'major', 'minor', 'large', 'small', 'great', 'grand'
        }
        
        # Geography terms
        geographies = [
            'amsterdam', 'london', 'paris', 'berlin', 'cologne', 'hamburg',
            'ottoman', 'byzantine',
            'boston', 'new york', 'pennsylvania',
            'india', 'bombay', 'calcutta', 'bengal',
            'britain', 'england', 'france', 'germany', 'holland', 'dutch'
        ]
        
        # Process each chunk
        for chunk in chunks:
            chunk_lower = chunk.lower()
            
            # Extract explicit relationship statements (PRIORITY - most reliable)
            
            # 1. ANCESTRY: "X descended from Y"
            ancestry_patterns = [
                r'([A-Z][a-z]+)\s+descended from\s+(?:(sephardi|ashkenazi|huguenot|quaker|parsee|hindu|brahmin|armenian|greek|protestant|court\s+jew)\s+)?([A-Z][a-z]+)',
                r'([A-Z][a-z]+).*?born to.*?(sephardi|ashkenazi|huguenot|quaker|parsee|hindu|brahmin|armenian|greek)',
            ]
            
            for pattern in ancestry_patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        family = match[0]
                        if len(match) == 3 and match[1]:  # Has identity
                            identity = match[1]
                            origin = match[2] if len(match) == 3 else None
                            norm_id = self._normalize_identity(identity.lower())
                            self.family_ancestry[family.lower()] = {
                                'origin_family': origin.lower() if origin else None,
                                'origin_identity': norm_id
                            }
                            self.explicit_identities[family.lower()].add(norm_id)
                            if origin:
                                self.explicit_identities[family.lower()].add(f'descended_from_{origin.lower()}')
                        elif len(match) == 2:
                            family, identity = match[0], match[1]
                            norm_id = self._normalize_identity(identity.lower())
                            self.explicit_identities[family.lower()].add(norm_id)
            
            # 2. CONVERSION: "X converted to Y" or "converted Jewish X"
            conversion_patterns = [
                r'([A-Z][a-z]+),?\s+(?:a\s+)?converted\s+(jewish|sephardi|protestant|christian|catholic|quaker|huguenot)',
                r'converted\s+(jewish|sephardi|protestant)\s+([A-Z][a-z]+)',
            ]
            
            for pattern in conversion_patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        # Determine which is family, which is identity
                        if match[0][0].isupper():  # First is family
                            family, identity = match[0], match[1]
                        else:  # Second is family
                            identity, family = match[0], match[1]
                        
                        norm_id = self._normalize_identity(identity.lower())
                        self.explicit_identities[family.lower()].add(norm_id)
                        self.explicit_identities[family.lower()].add('converted')
            
            # 3. KINLINKS: "X kinlinked with Y"
            kinlink_patterns = [
                r'([A-Z][a-z]+)\s+kinlinked with\s+([A-Z][a-z]+)',
                r'([A-Z][a-z]+)\s+married.*?([A-Z][a-z]+)',
                r'([A-Z][a-z]+)\s+partnered with\s+([A-Z][a-z]+)',
            ]
            
            for pattern in kinlink_patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        family1, family2 = match[0].lower(), match[1].lower()
                        self.family_cooccurrence[family1][family2] += 1
                        self.family_cooccurrence[family2][family1] += 1
            
            # 4. EXPLICIT COUSINHOOD MENTIONS: "X cousinhood included Y, Z families"
            cousinhood_patterns = [
                r'(jewish|quaker|huguenot|mennonite|parsee|hindu|armenian|greek|protestant|sephardi|ashkenazi|puritan|boston brahmin)\s+cousinhoods?\s+(?:included|comprised|consisted of|contained)\s+([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*)',
                r'cousinhoods?\s+(?:like|such as|including)\s+(jewish|quaker|huguenot|mennonite|parsee|hindu|armenian|greek|protestant|sephardi|ashkenazi|puritan)\s+([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*)',
            ]
            
            for pattern in cousinhood_patterns:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    if len(match) >= 2:
                        identity = match[0]
                        families_text = match[1]
                        # Extract all family names
                        family_names = re.findall(r'([A-Z][a-z]{3,})', families_text)
                        norm_id = self._normalize_identity(identity.lower())
                        for family in family_names:
                            family_lower = family.lower()
                            if family_lower not in self.noise_words:
                                self.identity_families[norm_id][family_lower] += 5  # Higher weight for explicit mention
                                self.explicit_identities[family_lower].add(norm_id)
            
            # Extract identity-family pairs with PRECISE patterns
            # Only match when identity term directly modifies the family name
            proper_names = re.findall(r'\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*\b', chunk)
            surnames = [name.split()[-1] for name in proper_names if len(name.split()[-1]) > 3]
            
            for identity in identities:
                if identity in chunk_lower:
                    # Precise patterns: identity must directly modify the surname
                    # Pattern 1: "Jewish Rothschild" or "Sephardi banker Mendes"
                    pattern1 = rf'\b{re.escape(identity)}\s+(?:\w+\s+)?([A-Z][a-z]{{3,}})\b'
                    # Pattern 2: "Rothschild, a Jewish" or "Mendes was Sephardi"
                    pattern2 = rf'\b([A-Z][a-z]{{3,}}),?\s+(?:a|an|the|was|were)\s+{re.escape(identity)}\b'
                    # Pattern 3: "the Jewish family of Rothschild"
                    pattern3 = rf'\b{re.escape(identity)}\s+(?:family|banker|merchant|trader)s?\s+(?:of\s+)?([A-Z][a-z]{{3,}})\b'
                    # Pattern 4: "Rothschild's Jewish origins"
                    pattern4 = rf'\b([A-Z][a-z]{{3,}})(?:\'s)?\s+{re.escape(identity)}\s+(?:origin|background|heritage|descent)\b'
                    
                    for pattern in [pattern1, pattern2, pattern3, pattern4]:
                        matches = re.findall(pattern, chunk, re.IGNORECASE)
                        for match in matches:
                            surname_lower = match.lower() if isinstance(match, str) else match[0].lower()
                            if surname_lower not in self.noise_words and len(surname_lower) > 3:
                                normalized_identity = self._normalize_identity(identity)
                                
                                # CRITICAL: Disambiguate "brahmin" based on context
                                if normalized_identity == 'brahmin':
                                    # Check if this is actually Boston Brahmin (Protestant) or Hindu Brahmin
                                    boston_context = any(term in chunk_lower for term in [
                                        'boston', 'massachusetts', 'harvard', 'new england',
                                        'puritan', 'cabot', 'lowell', 'forbes', 'perkins', 'adams'
                                    ])
                                    hindu_context = any(term in chunk_lower for term in [
                                        'india', 'hindu', 'bengal', 'bombay', 'calcutta',
                                        'caste', 'tagore', 'bania', 'maratha'
                                    ])
                                    
                                    if boston_context and not hindu_context:
                                        normalized_identity = 'boston_brahmin'
                                    elif hindu_context:
                                        normalized_identity = 'hindu'  # Hindu caste, not standalone brahmin
                                    # If neither clear context, skip to avoid confusion
                                    else:
                                        continue
                                
                                self.identity_families[normalized_identity][surname_lower] += 1
                                self.explicit_identities[surname_lower].add(normalized_identity)
            
            # Extract family co-occurrence
            for i, surname1 in enumerate(surnames):
                for surname2 in surnames[i+1:]:
                    if surname1 != surname2:
                        s1_lower = surname1.lower()
                        s2_lower = surname2.lower()
                        self.family_cooccurrence[s1_lower][s2_lower] += 1
                        self.family_cooccurrence[s2_lower][s1_lower] += 1
            
            # Extract family-geography pairs
            for surname in surnames:
                surname_lower = surname.lower()
                for geo in geographies:
                    if geo in chunk_lower:
                        self.family_geography[surname_lower][geo] += 1
        
        return self._build_results()
    
    def _normalize_identity(self, identity: str) -> str:
        """Normalize identity variants to canonical form."""
        identity = identity.lower()
        
        # Map variants to canonical
        # IMPORTANT: Check compound terms BEFORE single terms (boston brahmin before brahmin)
        mappings = {
            # Compound terms first (more specific)
            'boston brahmins': 'boston_brahmin', 'boston brahmin': 'boston_brahmin',
            'court jews': 'court_jew', 'court jew': 'court_jew',
            'irish catholic': 'catholic_irish', 'catholic irish': 'catholic_irish',
            'sino-thai': 'overseas_chinese', 'chinese thai': 'overseas_chinese',
            'overseas chinese': 'overseas_chinese',
            # Single terms
            'jews': 'jewish', 'jew': 'jewish',
            'quakers': 'quaker',
            'huguenots': 'huguenot',
            'mennonites': 'mennonite',
            'calvinists': 'calvinist',
            'presbyterians': 'presbyterian',
            'parsees': 'parsee', 'parsi': 'parsee', 'parsis': 'parsee',
            'hindus': 'hindu',
            'brahmins': 'brahmin',  # Ambiguous - will be disambiguated by context
            'banias': 'bania',
            'armenians': 'armenian',
            'greeks': 'greek',
            'puritans': 'puritan',
            'sephardi': 'sephardim', 'sephardic': 'sephardim',
            'ashkenazi': 'ashkenazim', 'ashkenazic': 'ashkenazim',
            'chaebols': 'chaebol'
        }
        
        return mappings.get(identity, identity)
    
    def _build_results(self) -> Dict:
        """Build structured results from extracted data."""
        
        # CLEANUP: Boston Brahmin (Protestant) and Hindu Brahmin are mutually exclusive
        families_with_boston_brahmin = set()
        if 'boston_brahmin' in self.identity_families:
            families_with_boston_brahmin = set(self.identity_families['boston_brahmin'].keys())
        
        # If a family is Boston Brahmin (Protestant), remove Hindu/"brahmin" tags
        if families_with_boston_brahmin:
            for family in families_with_boston_brahmin:
                # Remove generic "brahmin" tag
                if 'brahmin' in self.identity_families and family in self.identity_families['brahmin']:
                    del self.identity_families['brahmin'][family]
                # Remove "hindu" tag (Boston Brahmin are Protestant, not Hindu)
                if 'hindu' in self.identity_families and family in self.identity_families['hindu']:
                    del self.identity_families['hindu'][family]
                # Clean up explicit identities
                if family in self.explicit_identities:
                    self.explicit_identities[family].discard('brahmin')
                    self.explicit_identities[family].discard('hindu')
        
        results = {
            'cousinhoods': {},
            'statistics': {},
            'validation': {}
        }
        
        # Build cousinhoods (families with 3+ mentions, filtered for noise)
        for identity, families in self.identity_families.items():
            # Filter out noise words
            filtered_families = {
                f: count for f, count in families.items() 
                if count >= 3 and f not in self.noise_words and len(f) > 3
            }
            
            if filtered_families:
                # Sort by count
                sorted_families = sorted(filtered_families.items(), key=lambda x: x[1], reverse=True)
                
                # Get top families
                top_families = sorted_families[:25]
                
                # Get geography for this cousinhood
                geography = self._get_dominant_geography(sorted_families[:10])
                
                results['cousinhoods'][identity] = {
                    'families': [f for f, c in top_families],
                    'counts': {f: c for f, c in top_families},
                    'geography': geography
                }
        
        # Distinguish Boston Brahmin from Hindu Brahmin using geography
        if 'brahmin' in results['cousinhoods']:
            brahmin_data = results['cousinhoods']['brahmin']
            families_with_geo = []
            for family in brahmin_data['families']:
                geo = self.family_geography.get(family, {})
                # Check if more US or more India mentions
                us_count = geo.get('boston', 0) + geo.get('massachusetts', 0) + geo.get('america', 0)
                india_count = geo.get('india', 0) + geo.get('bengal', 0) + geo.get('calcutta', 0)
                
                if us_count > india_count:
                    families_with_geo.append(('boston_brahmin', family, brahmin_data['counts'][family]))
                elif india_count > 0:
                    families_with_geo.append(('hindu_brahmin', family, brahmin_data['counts'][family]))
            
            # Split into two groups
            boston = [(f, c) for g, f, c in families_with_geo if g == 'boston_brahmin']
            hindu = [(f, c) for g, f, c in families_with_geo if g == 'hindu_brahmin']
            
            if boston:
                results['cousinhoods']['boston_brahmin'] = {
                    'families': [f for f, c in boston],
                    'counts': {f: c for f, c in boston},
                    'geography': 'New England/America'
                }
            if hindu:
                results['cousinhoods']['hindu_brahmin'] = {
                    'families': [f for f, c in hindu],
                    'counts': {f: c for f, c in hindu},
                    'geography': 'India'
                }
            
            # Remove ambiguous 'brahmin' entry
            del results['cousinhoods']['brahmin']
        
        # Statistics
        results['statistics'] = {
            'total_identities_found': len(self.identity_families),
            'total_families_identified': sum(len(f) for f in self.identity_families.values()),
            'cousinhoods_detected': len(results['cousinhoods']),
            'noise_filtered': sum(1 for f in self.identity_families.values() for name in f.keys() if name in self.noise_words)
        }
        
        return results
    
    def _get_dominant_geography(self, top_families: List[Tuple[str, int]]) -> str:
        """Determine dominant geography for a cousinhood based on top families."""
        geo_counts = defaultdict(int)
        
        for family, _ in top_families:
            if family in self.family_geography:
                for geo, count in self.family_geography[family].items():
                    geo_counts[geo] += count
        
        if geo_counts:
            top_geo = sorted(geo_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            return ', '.join([g for g, c in top_geo])
        return 'Unknown'


def detect_cousinhoods_from_index(save_results: bool = False):
    """
    Run cousinhood detection on indexed documents.
    
    Args:
        save_results: If True, save detected cousinhoods to data/detected_cousinhoods.json
    """
    import json
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib.config import DATA_DIR
    
    # Load cached documents
    cache_dir = os.path.join(DATA_DIR, 'cache')
    chunks = []
    
    for filename in ['Thunderclap Part I.docx.cache.json', 
                     'Thunderclap Part II.docx.cache.json',
                     'Thunderclap Part III.docx.cache.json']:
        cache_file = os.path.join(cache_dir, filename)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text = data.get('text', '')
                # Split into rough chunks for processing
                words = text.split()
                for i in range(0, len(words), 500):
                    chunk = ' '.join(words[i:i+500])
                    chunks.append(chunk)
    
    print(f"Processing {len(chunks)} chunks...")
    
    detector = CousinoodDetector()
    results = detector.extract_from_documents(chunks)
    
    # Save results if requested
    if save_results:
        output_file = os.path.join(DATA_DIR, 'detected_cousinhoods.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n[SAVED] Detected cousinhoods saved to {output_file}")
    
    return results, detector


def validate_against_hardcoded():
    """Validate detected cousinhoods against hardcoded list."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib.cousinhoods import COUSINHOODS
    
    results, detector = detect_cousinhoods_from_index()
    
    # Add detector to results for later access
    results['detector'] = detector
    
    # Map hardcoded keys to detected keys
    key_mapping = {
        'jewish_sephardim': 'sephardim',
        'jewish_ashkenazim': 'ashkenazim',
        'jewish_court': 'court_jew',
        'quaker': 'quaker',
        'huguenot': 'huguenot',
        'mennonite': 'mennonite',
        'puritan': 'puritan',
        'boston_brahmin': 'boston_brahmin',
        'parsee': 'parsee',
        'armenian': 'armenian',
        'greek': 'greek'
    }
    
    validation = {}
    
    for hardcoded_key, detected_key in key_mapping.items():
        hardcoded = COUSINHOODS.get(hardcoded_key, {})
        detected = results['cousinhoods'].get(detected_key, {})
        
        if not hardcoded:
            continue
        
        # Extract family surnames from hardcoded (strip italics, extras)
        hardcoded_families = []
        for fam in hardcoded.get('families', []):
            # Extract just surname (last word, remove italics/parentheses)
            clean = fam.replace('*', '').split('(')[0].strip().split()[-1].lower()
            hardcoded_families.append(clean)
        
        detected_families = detected.get('families', [])
        
        # Check matches
        found = [f for f in hardcoded_families if f in detected_families]
        missing = [f for f in hardcoded_families if f not in detected_families]
        extra = [f for f in detected_families[:10] if f not in hardcoded_families]
        
        validation[hardcoded_key] = {
            'hardcoded_count': len(hardcoded_families),
            'detected_count': len(detected_families),
            'found': found,
            'missing': missing,
            'extra_found': extra,
            'match_rate': len(found) / len(hardcoded_families) if hardcoded_families else 0
        }
    
    return results, validation


if __name__ == "__main__":
    # Run with save_results=True to cache detected cousinhoods
    results, detector = detect_cousinhoods_from_index(save_results=True)
    
    # Validate against hardcoded
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib.cousinhoods import HARDCODED_COUSINHOODS
    
    validation = {}
    key_mapping = {
        'jewish_sephardim': 'sephardim',
        'jewish_ashkenazim': 'ashkenazim',
        'jewish_court': 'court_jew',
        'quaker': 'quaker',
        'huguenot': 'huguenot',
        'mennonite': 'mennonite',
        'puritan': 'puritan',
        'boston_brahmin': 'boston_brahmin',
        'parsee': 'parsee',
        'armenian': 'armenian',
        'greek': 'greek'
    }
    
    for hardcoded_key, detected_key in key_mapping.items():
        hardcoded = HARDCODED_COUSINHOODS.get(hardcoded_key, {})
        detected = results['cousinhoods'].get(detected_key, {})
        
        if not hardcoded:
            continue
        
        # Extract family surnames from hardcoded (strip italics, extras)
        hardcoded_families = []
        for fam in hardcoded.get('families', []):
            clean = fam.replace('*', '').split('(')[0].strip().split()[-1].lower()
            hardcoded_families.append(clean)
        
        detected_families = detected.get('families', [])
        
        # Check matches
        found = [f for f in hardcoded_families if f in detected_families]
        missing = [f for f in hardcoded_families if f not in detected_families]
        extra = [f for f in detected_families[:10] if f not in hardcoded_families]
        
        validation[hardcoded_key] = {
            'hardcoded_count': len(hardcoded_families),
            'detected_count': len(detected_families),
            'found': found,
            'missing': missing,
            'extra_found': extra,
            'match_rate': len(found) / len(hardcoded_families) if hardcoded_families else 0
        }
    
    print("\n" + "="*80)
    print("COUSINHOOD DETECTION RESULTS")
    print("="*80)
    
    print(f"\nStatistics:")
    for key, value in results['statistics'].items():
        print(f"  {key}: {value}")
    
    # Show explicit ancestry statements found
    if detector and detector.family_ancestry:
        print(f"\n{'='*80}")
        print("EXPLICIT ANCESTRY STATEMENTS (FROM DOCUMENTS)")
        print("="*80)
        for family, ancestry in sorted(detector.family_ancestry.items())[:20]:
            origin_fam = ancestry.get('origin_family', '')
            origin_id = ancestry.get('origin_identity', '')
            if origin_fam:
                print(f"  {family.capitalize()} descended from {origin_id.capitalize()} {origin_fam.capitalize()}")
            else:
                print(f"  {family.capitalize()} has {origin_id.capitalize()} ancestry")
    
    # Show families with explicit identity labels
    if detector and detector.explicit_identities:
        print(f"\n{'='*80}")
        print("FAMILIES WITH EXPLICIT IDENTITY LABELS")
        print("="*80)
        for family, identities in sorted(detector.explicit_identities.items())[:30]:
            if len(identities) > 0 and family not in detector.noise_words:
                ids = ', '.join(sorted(identities))
                print(f"  {family.capitalize():<20} = {ids}")
    
    print(f"\n{'='*80}")
    print("VALIDATION AGAINST HARDCODED LIST")
    print("="*80)
    
    total_match = 0
    total_hardcoded = 0
    
    for cousinhood, val in sorted(validation.items()):
        print(f"\n{cousinhood.upper().replace('_', ' ')}:")
        print(f"  Hardcoded families: {val['hardcoded_count']}")
        print(f"  Detected families: {val['detected_count']}")
        print(f"  Match rate: {val['match_rate']*100:.0f}%")
        
        if val['found']:
            print(f"  [FOUND] {', '.join(val['found'][:10])}")
        if val['missing']:
            print(f"  [MISSING] {', '.join(val['missing'][:5])}")
        if val['extra_found']:
            print(f"  [EXTRA] {', '.join(val['extra_found'][:5])}")
        
        total_match += len(val['found'])
        total_hardcoded += val['hardcoded_count']
    
    print(f"\n{'='*80}")
    print(f"OVERALL: {total_match}/{total_hardcoded} families found ({total_match/total_hardcoded*100:.0f}% match rate)")
    print("="*80)
    
    print(f"\n{'='*80}")
    print("TOP 10 FAMILIES PER COUSINHOOD (DETECTED)")
    print("="*80)
    
    for identity, data in sorted(results['cousinhoods'].items()):
        print(f"\n{identity.upper().replace('_', ' ')} ({data.get('geography', 'Unknown')}):")
        for family, count in list(data['counts'].items())[:10]:
            print(f"  {family:<20} ({count} mentions)")

