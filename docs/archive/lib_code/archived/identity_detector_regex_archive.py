"""
Identity & Attribute Detector - Extracts demographic and identity attributes of banking families.

This detector identifies:
- Religious/ethnic identities (Jewish, Quaker, Huguenot, Hindu, Parsee, Armenian, Greek, etc.)
- Religious sub-groups (Sephardi, Ashkenazi, Boston Brahmin, Overseas Chinese, etc.)
- Gender attributes (female, woman, widow)
- Racial identity (Black - regardless of geography)
- Nationality identity (American, British, French, German, etc. - when identifying person's nationality)
- Social status (Court Jew, converted, etc.)

NOTE: Nationality is tracked as IDENTITY (e.g., "German banker Warburg"), NOT as geography.
Continental terms (African, European, Asian) are NOT tracked as they conflate geography with identity.

Note: This is NOT a identity detector. identitys are small intermarried elite families 
(actual cousins/in-laws through repeated kinlinks), whereas this detector finds broader 
identity attributes that apply to all members of a category (e.g., all Jews, all women bankers).
"""

import re
import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class IdentityDetector:
    """Detects identity and demographic attributes of banking families from document text."""
    
    def __init__(self):
        # NOTE: "families" is a misnomer for individual attributes like LGBT, Latino
        # For hereditary: jewish -> rothschild family (all Rothschilds are Jewish)
        # For individual: lgbt -> bostic (Raphael Bostic is LGBT, not all Bostics)
        # Using surname for consistency, but semantics differ by identity type
        self.identity_families = defaultdict(lambda: defaultdict(int))  # identity -> surname -> count
        self.family_cooccurrence = defaultdict(lambda: defaultdict(int))  # family -> family -> count
        self.family_geography = defaultdict(lambda: defaultdict(int))  # family -> geography -> count
        self.family_ancestry = {}  # family -> {origin_family, origin_identity}
        self.explicit_identities = defaultdict(set)  # surname -> set of identities explicitly stated
        
        # Pre-compile regex patterns for speed (compiled once, not per chunk)
        self._compiled_patterns = {}
        self._identity_terms_set = None  # Lazy loaded
    
    def extract_from_documents(self, chunks: List[str]) -> Dict:
        """
        Extract identity/attribute patterns from document chunks.
        
        Args:
            chunks: List of document text chunks
        
        Returns:
            Dictionary with detected patterns
        """
        print("Detecting identity & attribute patterns from documents...")
        
        # Identity/attribute terms to search for
        identities = [
            # Religious/ethnic (general -> specific)
            'jew', 'jews', 'jewish',
            'sephardim', 'sephardi', 'sephardic',
            'ashkenazim', 'ashkenazi', 'ashkenazic',
            'court jew', 'court jews',
            'quaker', 'quakers',
            'huguenot', 'huguenots',
            'mennonite', 'mennonites',
            'calvinist', 'calvinists',
            'presbyterian', 'presbyterians',
            'puritan', 'puritans',
            'boston brahmin', 'boston brahmins',
            'catholic irish', 'irish catholic',
            'parsee', 'parsees', 'parsi',
            'hindu', 'hindus',
            'brahmin', 'brahmins',
            'muslim', 'muslims', 'islam', 'islamic', 'sunni', 'shia', 'shiite',  # Muslim/Islamic bankers
            'bania', 'banias',
            'armenian', 'armenians',
            'greek', 'greeks',
            'lebanese', 'lebanon', 'maronite', 'maronites',  # Lebanese banking families
            'palestinian', 'palestine',  # Palestinian bankers (often in Lebanon/diaspora)
            'overseas chinese', 'sino-thai', 'chinese thai',
            'chaebol', 'chaebols',
            'zaibatsu',
            # Gender attributes (widow merged into female, royal titles included)
            'woman', 'women', 'female', 'widow', 'widows',
            'queen', 'princess', 'lady',  # Female royal/elite titles
            # Racial identity attributes
            'black', 'blacks',
            'african american', 'african-american',
            # African ethnic groups (under Black racial category)
            'hausa', 'yoruba', 'igbo', 'fulani', 'akan', 'zulu',
            'nigerian', 'ghanaian', 'kenyan', 'south african',
            # Ethnic/cultural identity attributes
            'latino', 'latina', 'latinos', 'latinas',
            'hispanic', 'hispanics',
            'puerto rican', 'mexican', 'mexican-american',
            'basque', 'basques',  # Basque ethnic group (Spain/France)
            'native american', 'american indian', 'lumbee',  # Indigenous peoples of Americas
            # NOTE: Removed LGBT - better to use keyword search for context, not individual tagging
            # LGBT is about context (lavender marriages, AIDS crisis, homophobia), not individual surnames
            # Searching "gay bankers" finds chunks with those keywords, which is what we want
            # Ethnic identities (NOT civic nationalities)
            'scottish', 'scots',  # Ethnic group
            'irish',  # Ethnic (distinct from Catholic Irish which is already tracked)
            'welsh',
            # NOTE: Removed civic nationality tracking (american, british, french, german, russian, etc.)
            # Reason: Nationalities are civic, not ethnic/racial/religious identities
            # Keep: Black (racial), Jewish (religious/ethnic), Scottish (ethnic), Irish (ethnic)
            # Remove: American, British, French, German, Russian (civic nationalities only)
        ]
        
        # Noise words to exclude (generic terms, not family names)
        self.noise_words = {
            # Identity terms themselves
            'jew', 'jews', 'jewish', 'quaker', 'quakers', 'huguenot', 'huguenots',
            'parsee', 'parsees', 'hindu', 'hindus', 'brahmin', 'brahmins',
            'armenian', 'armenians', 'greek', 'greeks', 'puritan', 'puritans',
            'sephardi', 'sephardim', 'ashkenazi', 'ashkenazim', 'mennonite', 'mennonites',
            'calvinist', 'calvinists', 'presbyterian', 'presbyterians',
            # NOTE: Removed Asian groups from noise - they should be detected!
            # 'overseas', 'chinese', 'chaebol', 'chaebols', 'zaibatsu',
            'bania', 'banias', 'maratha', 'marathas',
            'woman', 'women', 'female',  # widow merged into female
            'black', 'blacks', 'white', 'caucasian',
            'latino', 'latina', 'latinos', 'latinas', 'hispanic', 'hispanics',
            'scottish', 'scots', 'welsh',
            # LGBT removed from noise - it's just a keyword, not an identity to extract
            'gay',  # Add to noise to prevent "Claudine Gay" false positive
            # Business terms
            'bank', 'banks', 'banker', 'bankers', 'banking',
            'company', 'companies', 'firm', 'firms', 'house', 'houses',
            'merchant', 'merchants', 'trader', 'traders', 'trading',
            'partner', 'partners', 'partnership', 'agent', 'agents',
            'labor', 'labour',  # Prevent "labor" from being detected as Latino
            'court', 'rabbi', 'protestant', 'catholic',
            # Company/institution names that get captured
            'city', 'citi', 'prudential', 'continental', 'budget', 'business',
            'coast', 'penny', 'national', 'federal', 'trust',
            'hospital', 'liberty', 'science', 'insurance', 'detroit',
            'south', 'rock', 'supreme', 'universal', 'consolidated',
            'security', 'savings', 'mutual', 'equitable', 'chemical',
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
            'haiti', 'harlem', 'memphis', 'ghana', 'nigeria', 'lagos',
            'jamaica', 'trinidad', 'barbados', 'caribbean', 'senegal',
            # National adjectives that are ONLY geographic context (not identity)
            'turkish', 'austrian', 'austro', 'anglo', 'bavarian', 'belgian',
            'chinese', 'japanese', 'scottish',
            # Note: french, german, british, italian, spanish, portuguese, dutch, russian, american
            # are REMOVED from noise - they can be identity attributes when modifying family names
            # Common words that appear capitalized
            'this', 'that', 'their', 'these', 'those', 'with', 'from', 'into',
            'although', 'among', 'amidst', 'another', 'after', 'along',
            'since', 'however', 'along', 'over', 'under', 'until', 'during',
            'while', 'where', 'when', 'which', 'about', 'above', 'across',
            # Titles and political terms
            'parliament', 'congress', 'assembly', 'senate', 'council',
            'king', 'queen', 'prince', 'princess', 'emperor', 'duke',
            'president', 'general', 'minister', 'chancellor', 'secretary',
            'governor', 'senator', 'representative', 'ambassador',
            # Common first names (only when standalone - surnames like Jordan, McGuire are OK)
            'charles', 'george', 'william', 'henry', 'john', 'james',
            'robert', 'david', 'thomas', 'joseph', 'edward', 'richard',
            'michael', 'daniel', 'samuel', 'alexander', 'benjamin',
            'martin', 'anna', 'alonzo', 'maggie', 'bruce', 'marshall',
            'clinton', 'auguste', 'director', 'perella', 'claiborne', 'rivlin',
            # Note: vernon, raymond, eugene, frank, roger, kenneth, reginald
            # are NOT in noise because they can be surnames (Jordan, McGuire, Rice, Raines, Ferguson, Chenault, Lewis)
            # Regional identifiers (ONLY geographic context, not identity)
            'scots', 'irish', 'welsh', 'european', 'asian', 'middle',
            # Note: english, french, german, british are REMOVED - they can be identity attributes
            # Institutions
            'harvard', 'yale', 'oxford', 'cambridge',
            'microsoft', 'google', 'facebook', 'apple',
            # Time/measurement terms
            'years', 'century', 'decades', 'period', 'times', 'months',
            # Generic descriptors
            'many', 'some', 'several', 'various', 'other', 'others',
            'major', 'minor', 'large', 'small', 'great', 'grand',
            # Common false positives for Latino/LGBT detection (removed 'diaz' - it's a real Latino surname!)
            'islands', 'francisco', 'fannie', 'virgin', 'york',
            'theresa', 'emmanuel', 'teresa', 'maria', 'marie',
            'cooke', 'cookes',  # Jay Cooke (not LGBT, just mentioned near lavender)
            'rockefeller', 'nixon', 'bush', 'daughter', 'communications', 'rican',  # Not Latino despite proximity
            'frans', 'jacob', 'adult', 'danzig', 'invested', 'related', 'johanna', 'textile',  # Generic words
            'sector', 'southeast', 'asian', 'equity',  # Geographic/generic terms, not family names
            'lumbee', 'guaranty',  # Lumbee Guaranty Bank - tribe name and bank term, not surnames
            'lumbee', 'guaranty', 'cherokee', 'navajo',  # Tribal/bank names, not surnames
            'monopolized', 'tribes', 'peers', 'goods', 'forces', 'affairs', 'legalized', 'estate',  # Generic words
            'syria', 'muslims', 'christian', 'jordan', 'capitulatory',  # Geographic/religious terms, not surnames
            'brotherhood', 'rulers', 'regime', 'aristocracy', 'moriscos', 'farrukhsiyar',  # Muslim noise
            'refugees', 'assassinated', 'founded', 'financiers', 'students', 'authority', 'development',  # Palestinian noise
            'party', 'colony', 'rand', 'market', 'shares', 'exploration', 'diamonds', 'mining',  # South African noise
            'chief', 'chiefs', 'dynasty', 'arrived', 'gained',  # Yoruba/tribal noise
            'hire', 'turn', 'held', 'political', 'jerusalem', 'jaffa',  # Generic noise
            'seat', 'hold', 'head', 'central', 'took', 'prospered', 'children', 'adolphe',  # Female noise
            'empire', 'bucharest', 'deflect', 'expel', 'creating', 'unlike', 'funded',  # More generic noise
            'fire', 'namibian', 'interpreter', 'criticize', 'diasporas', 'investment',  # More noise
            'declined', 'manufactures', 'cloths', 'official', 'tribe', 'courtiers', 'interpreters',  # Hausa/Muslim noise
            'exports', 'started', 'corp', 'paper', 'supply', 'magnate', 'uranium', 'planters',  # More generic noise
            'mohamed', 'alickaj',  # Common Muslim first names, not surnames
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
            
            # 4. EXPLICIT identity MENTIONS: "X identity included Y, Z families"
            identity_patterns = [
                r'(jewish|quaker|huguenot|mennonite|parsee|hindu|armenian|greek|protestant|sephardi|ashkenazi|puritan|boston brahmin)\s+identitys?\s+(?:included|comprised|consisted of|contained)\s+([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*)',
                r'identitys?\s+(?:like|such as|including)\s+(jewish|quaker|huguenot|mennonite|parsee|hindu|armenian|greek|protestant|sephardi|ashkenazi|puritan)\s+([A-Z][a-z]+(?:,?\s+(?:and\s+)?[A-Z][a-z]+)*)',
            ]
            
            for pattern in identity_patterns:
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
            
            # OPTIMIZATION: Only check identities that appear in this chunk
            for identity in identities:
                if identity not in chunk_lower:
                    continue  # Skip identities not in this chunk (saves ~50% processing)
                
                # Precise patterns: identity must directly modify the surname
                
                # SPECIAL HANDLING FOR BLACK IDENTITY (extract names, not context words)
                if identity in ['black', 'blacks']:
                    # Only extract FULL NAMES from narrow, high-confidence patterns
                    # Pattern 1: "FirstName LastName the first Black position"
                    black_pattern1 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+the\s+first\s+[Bb]lack\s+(?:Governor|CEO|Chair|president|director|partner|woman|man)'
                    # Pattern 2: "first Black position since FirstName LastName"
                    black_pattern2 = r'first\s+[Bb]lack.*?since\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 3: "Nigerian-born FirstName LastName"
                    black_pattern3 = r'(?:Nigerian|Haitian|Guyanese|Barbadian)-born\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 4: "FirstName LastName, a Black role"
                    black_pattern4 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+),\s+a\s+[Bb]lack\s+(?:banker|lawyer|executive|partner|director)'
                    # Pattern 5: "FirstName LastName became/named first Black"
                    black_pattern5 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:became|as)\s+(?:the\s+)?first\s+[Bb]lack'
                    # Pattern 6: "named/appointed FirstName LastName the first Black"
                    black_pattern6 = r'(?:named|appointed)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:the|as)\s+first\s+[Bb]lack'
                    # Pattern 7: "co-racial FirstName LastName"
                    black_pattern7 = r'co-racial,?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 8: "Black elite FirstName LastName" or context
                    black_pattern8 = r'[Bb]lack\s+elite.{1,30}?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 9: "Blacks broke... FirstName LastName" (within 100 chars)
                    black_pattern9 = r'[Bb]lacks\s+(?:also\s+)?(?:broke|thrived|made).{1,100}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 10: "FirstName LastName's first Black" (like "Morgan Stanley's first Black MD")
                    black_pattern10 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+).{1,50}?first\s+[Bb]lack'
                    
                    for pattern in [black_pattern1, black_pattern2, black_pattern3, black_pattern4,
                                    black_pattern5, black_pattern6, black_pattern7, black_pattern8,
                                    black_pattern9, black_pattern10]:
                        matches = re.findall(pattern, chunk)
                        for match in matches:
                            # Extract surname from full name
                            full_name = match if isinstance(match, str) else match[0]
                            surname_lower = full_name.strip().split()[-1].lower()
                            if surname_lower not in self.noise_words and len(surname_lower) > 3:
                                self.identity_families['black'][surname_lower] += 1
                                self.explicit_identities[surname_lower].add('black')
                    continue  # Skip generic patterns for Black
                
                # SPECIAL HANDLING FOR LEBANESE IDENTITY
                # Lebanese families often described with religious sub-identity (Greek Orthodox, Maronite)
                if identity in ['lebanese', 'lebanon', 'maronite', 'maronites']:
                    # Pattern 1: "Lebanese FirstName LastName" or "Lebanese elites/Christians"
                    lebanese_pattern1 = r'Lebanese\s+(?:elites?|Christians?)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                    # Pattern 2: "Lebanon's... FirstName LastName" (wide window)
                    lebanese_pattern2 = r'Lebanon.{0,20}(?:the\s+)?(?:Greek Orthodox|Greek Catholic|Maronite)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                    # Pattern 2b: "Greek Orthodox Sursock" in Lebanese context (check for Lebanon nearby)
                    lebanese_pattern2b = r'(?:Greek Orthodox|Greek Catholic)\s+([A-Z][a-z]+)' if 'lebanon' in chunk_lower else None
                    # Pattern 3: "Maronite FirstName LastName"
                    lebanese_pattern3 = r'Maronite\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                    # Pattern 4: "Greek Catholic (Maronite) FirstName LastName"
                    lebanese_pattern4 = r'Greek Catholic.*?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 5: "fled Lebanon... FirstName LastName"
                    lebanese_pattern5 = r'fled Lebanon.{0,50}?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                    # Pattern 6: "son of Lebanese immigrants, FirstName LastName"
                    lebanese_pattern6 = r'son of Lebanese immigrants.{0,50}?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
                    # Pattern 7: "FirstName LastName, son of Lebanese"
                    lebanese_pattern7 = r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:the\s+)?son of Lebanese'
                    # Pattern 8: "born in Kuwait to Lebanese parents, FirstName LastName"
                    lebanese_pattern8 = r'(?:born in|to) Lebanese parents.{0,50}?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 9: Extract ALL names from list after "Lebanese Christians fleeing..."
                    if 'lebanese christians fleeing' in chunk_lower:
                        # Find the Lebanese Christians section
                        match_obj = re.search(r'Lebanese Christians fleeing.{0,600}', chunk)
                        if match_obj:
                            lebanese_section = match_obj.group()
                            # Extract all "FirstName LastName" patterns in this section
                            all_names = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:sold|became|led|held|was|joined)', lebanese_section)
                            for full_name in all_names:
                                surname_lower = full_name.strip().split()[-1].lower()
                                if surname_lower not in self.noise_words and len(surname_lower) > 3:
                                    self.identity_families['lebanese'][surname_lower] += 1
                                    self.explicit_identities[surname_lower].add('lebanese')
                    lebanese_pattern9 = None  # Handled above
                    
                    patterns = [p for p in [lebanese_pattern1, lebanese_pattern2, lebanese_pattern3, lebanese_pattern4, lebanese_pattern5,
                               lebanese_pattern6, lebanese_pattern7, lebanese_pattern8, lebanese_pattern9] if p is not None]
                    if lebanese_pattern2b:
                        patterns.append(lebanese_pattern2b)
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, chunk)
                        for match in matches:
                            full_name = match if isinstance(match, str) else match[0]
                            surname_lower = full_name.strip().split()[-1].lower()
                            if surname_lower not in self.noise_words and len(surname_lower) > 3:
                                self.identity_families['lebanese'][surname_lower] += 1
                                self.explicit_identities[surname_lower].add('lebanese')
                    continue  # Skip generic patterns for Lebanese
                
                # SPECIAL HANDLING FOR LATINO/HISPANIC IDENTITY
                if identity in ['latino', 'latina', 'hispanic', 'puerto rican', 'mexican', 'mexican-american', 'basque', 'basques']:
                    # Pattern 1: "Puerto Rican/Mexican/etc FirstName LastName"
                    # Covers ALL Latin American countries (Honduras, Colombia, etc.)
                    latino_countries = r'(?:Puerto Rican|Mexican|Colombian|Honduran|Venezuelan|Guatemalan|Salvadoran|Dominican|Cuban|Argentinian|Chilean|Peruvian|Ecuadorian|Bolivian|Paraguayan|Uruguayan|Costa Rican|Panamanian|Nicaraguan|Haitian|Jamaican|Barbadian|Trinidadian|Brazilian|Basque)'
                    latino_pattern1 = rf'{latino_countries}\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 2: "FirstName LastName became the first Latina/Hispanic"
                    latino_pattern2 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+became\s+the\s+first\s+(?:Latina?|Hispanic)'
                    # Pattern 3: "appointed FirstName LastName, the first Latina/Hispanic"
                    latino_pattern3 = r'(?:appointed|named)\s+([A-Z][a-z]+\s+[A-Z][a-z]+).{0,20}first\s+(?:Latina?|Hispanic)'
                    # Pattern 4: "first Latina/Hispanic... to serve... FirstName LastName"
                    latino_pattern4 = r'first\s+(?:Latina?|Hispanic).{0,50}?to\s+serve.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 5: "FirstName LastName, a Latino/Latina/Hispanic banker"
                    latino_pattern5 = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+),\s+a\s+(?:Latina?|Hispanic)(?:\s+(?:banker|executive))?'
                    # Pattern 6: "Cuban/etc refugee FirstName LastName"
                    latino_pattern6 = rf'{latino_countries}\s+(?:refugee|exile)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 7: "FirstName LastName... first Hispanic-owned bank" (look BACK from "first Hispanic-owned")
                    latino_pattern7 = r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,150}?first\s+Hispanic-owned\s+bank'
                    # Pattern 8: "FirstName LastName... he/she identified as Hispanic"
                    latino_pattern8 = r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,100}?(?:he|she)\s+identified\s+as\s+Hispanic'
                    # Pattern 9: "daughter of... Puerto Rican... FirstName LastName" (reverse order)
                    latino_pattern9 = r'daughter\s+of.{0,100}Puerto Rican.{0,100}?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 10: "FirstName LastName joined/worked... until... appointed her/him as first Hispanic"  
                    latino_pattern10 = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:joined|worked|served).{10,150}?appointed\s+(?:her|him)\s+as\s+the\s+first\s+(?:Latina?|Hispanic)' 
                    # Pattern 11: "daughter... Puerto Rican immigrant, FirstName LastName"
                    latino_pattern11 = r'Puerto Rican\s+immigrant.{0,50}?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 12: "appointed FirstName LastName as the first non-White" (with Unicode support for ñ, etc.)
                    latino_pattern12 = r'appointed\s+([A-Z][a-zA-Z\u00c0-\u017f]+\s+[A-Z][a-zA-Z\u00c0-\u017f]+)\s+as\s+the\s+first\s+non-White'
                    # Pattern 13: "FirstName LastName was... (Goldman/Morgan/etc)... identified as Hispanic" (wide window)
                    latino_pattern13 = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+was.{0,400}?(?:Goldman|Morgan|Lazard|Citi|CSFB|bank).{0,400}?identified\s+as\s+Hispanic'
                    # Pattern 14: "Lumbee Guaranty Bank" or "Native American owned bank" -> extract "Lumbee"
                    native_pattern1 = r'(Lumbee|Cherokee|Navajo|Sioux|Apache|Choctaw|Creek|Seminole)\s+(?:Guaranty\s+)?Bank'
                    # Pattern 15: "FirstName LastName... Native American banker/owned"
                    native_pattern2 = r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,100}?Native American\s+(?:banker|owned|tribe)'
                    # Pattern 16: "Basque-born FirstName LastName" (for Bassoco)
                    basque_pattern1 = r'Basque-born\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 17: "Gentile José Ramón Vial Lopez-Doriga" or similar Spanish compound names
                    spanish_pattern1 = r'(?:Gentile|hired)\s+([A-Z][a-zé]+\s+[A-Z][a-zéó]+\s+[A-Z][a-z]+-[A-Z][a-z]+)'
                    
                    for pattern in [latino_pattern1, latino_pattern2, latino_pattern3, latino_pattern4, latino_pattern5,
                                   latino_pattern6, latino_pattern7, latino_pattern8, latino_pattern9, latino_pattern10,
                                   latino_pattern11, latino_pattern12, latino_pattern13, native_pattern1, native_pattern2,
                                   basque_pattern1, spanish_pattern1]:
                        matches = re.findall(pattern, chunk)
                        for match in matches:
                            full_name = match if isinstance(match, str) else match[0]
                            surname_lower = full_name.strip().split()[-1].lower()
                            if surname_lower not in self.noise_words and len(surname_lower) > 2:  # Allow "Vial" (4 chars)
                                # Categorize into sub-identities
                                if identity in ['basque', 'basques']:
                                    self.identity_families['basque'][surname_lower] += 1
                                    self.explicit_identities[surname_lower].add('basque')
                                elif identity in ['native american', 'american indian', 'lumbee']:
                                    self.identity_families['native_american'][surname_lower] += 1
                                    self.explicit_identities[surname_lower].add('native_american')
                                else:
                                    # Latino/Hispanic
                                    self.identity_families['latino'][surname_lower] += 1
                                    self.explicit_identities[surname_lower].add('latino')
                    continue  # Skip generic patterns for Latino/Hispanic/Basque/Native American
                
                # SPECIAL HANDLING FOR LEBANESE IDENTITY
                if identity == 'lebanese':
                    # Pattern 1: "Lebanese FirstName LastName"
                    lebanese_pattern1 = r'Lebanese[- ](?:born\s+)?([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 2: "FirstName LastName... Lebanon PM/President/Minister"
                    lebanese_pattern2 = r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}?Lebanon(?:ese)?\s+(?:PM|President|Minister|Finance Minister)'
                    # Pattern 3: "Lebanon PM/President FirstName LastName"
                    lebanese_pattern3 = r'Lebanon(?:ese)?\s+(?:PM|President|Minister)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
                    # Pattern 4: "FirstName LastName, Lebanese banker"
                    lebanese_pattern4 = r'([A-Z][a-z]+\s+[A-Z][a-z]+),\s+Lebanese\s+(?:banker|financier)'
                    
                    for pattern in [lebanese_pattern1, lebanese_pattern2, lebanese_pattern3, lebanese_pattern4]:
                        matches = re.findall(pattern, chunk)
                        for match in matches:
                            full_name = match if isinstance(match, str) else match[0]
                            surname_lower = full_name.strip().split()[-1].lower()
                            if surname_lower not in self.noise_words and len(surname_lower) > 2:
                                self.identity_families['lebanese'][surname_lower] += 1
                                self.explicit_identities[surname_lower].add('lebanese')
                    continue  # Skip generic patterns for Lebanese
                
                # LGBT REMOVED - Use keyword search instead of individual tagging
                # Reason: LGBT is about context (lavender marriages, AIDS, homophobia)
                # not tagging individuals (Drexel mentioned in 100+ non-LGBT chunks)
                # Keyword search finds: "gay", "lgbt", "homosexual", "bisexual", "lavender", "aids"
                
                # Generic patterns for other identities
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
                                else:
                                    # If neither clear context, skip to avoid confusion
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
            'african american': 'african_american', 'african-american': 'african_american',
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
            'chaebols': 'chaebol',
            # Gender attributes (widow merged into female)
            'women': 'female', 'woman': 'female',
            'widows': 'female', 'widow': 'female',
            'blacks': 'black',
            # Nationality identities
            'americans': 'american',
            'germans': 'german',
            'italians': 'italian',
            'russians': 'russian',
            'english': 'british'  # Normalize English to British for consistency
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
            'identities': {},
            'statistics': {},
            'validation': {}
        }
        
        # Build identity groups (all detected families, filtered only for noise)
        for identity, families in self.identity_families.items():
            # Filter out noise words only (no minimum count requirement)
            filtered_families = {
                f: count for f, count in families.items() 
                if f not in self.noise_words and len(f) > 3
            }
            
            if filtered_families:
                # Sort by count
                sorted_families = sorted(filtered_families.items(), key=lambda x: x[1], reverse=True)
                
                # Get top families
                top_families = sorted_families[:25]
                
                # Get geography for this identity
                geography = self._get_dominant_geography(sorted_families[:10])
                
                # Label appropriately: "individuals" for LGBT/Latino, "families" for hereditary
                label = 'individuals' if identity in ['lgbt', 'latino'] else 'families'
                
                results['identities'][identity] = {
                    label: [f for f, c in top_families],
                    'counts': {f: c for f, c in top_families},
                    'geography': geography,
                    'type': 'individual' if identity in ['lgbt', 'latino'] else 'hereditary'
                }
        
        # Statistics
        results['statistics'] = {
            'total_identities_found': len(self.identity_families),
            'total_families_identified': sum(len(f) for f in self.identity_families.values()),
            'identities_detected': len(results['identities']),
            'noise_filtered': sum(1 for f in self.identity_families.values() for name in f.keys() if name in self.noise_words)
        }
        
        return results
    
    def _get_dominant_geography(self, top_families: List[Tuple[str, int]]) -> str:
        """Determine dominant geography for an identity based on top families."""
        geo_counts = defaultdict(int)
        
        for family, _ in top_families:
            if family in self.family_geography:
                for geo, count in self.family_geography[family].items():
                    geo_counts[geo] += count
        
        if geo_counts:
            top_geo = sorted(geo_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            return ', '.join([g for g, c in top_geo])
        return 'Unknown'


def detect_identities_from_index(save_results: bool = False):
    """
    Run identity detection on indexed documents.
    
    Args:
        save_results: If True, save detected identities to data/detected_identities.json
    """
    import json
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from lib.config import DATA_DIR, CACHE_DIR
    from lib.index_builder import split_into_chunks
    
    # Load cached documents and split using standard chunking (no duplication)
    chunks = []
    
    for filename in ['Thunderclap Part I.docx.cache.json', 
                     'Thunderclap Part II.docx.cache.json',
                     'Thunderclap Part III.docx.cache.json']:
        cache_file = os.path.join(CACHE_DIR, filename)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                text = data.get('text', '')
                # Reuse standard chunking function (no duplication)
                doc_chunks = split_into_chunks(text)
                chunks.extend(doc_chunks)
    
    print(f"Processing {len(chunks)} chunks...")
    
    detector = IdentityDetector()
    results = detector.extract_from_documents(chunks)
    
    # Save results if requested
    if save_results:
        # Save to detected_identities.json (renamed from detected_identitys.json)
        output_file = os.path.join(DATA_DIR, 'detected_identities.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n[SAVED] Detected identities saved to {output_file}")
    
    return results, detector


if __name__ == "__main__":
    # Run with save_results=True to cache detected identities
    results, detector = detect_identities_from_index(save_results=True)
    
    print("\n" + "="*80)
    print("IDENTITY & ATTRIBUTE DETECTION RESULTS")
    print("="*80)
    
    print(f"\nStatistics:")
    for key, value in results['statistics'].items():
        print(f"  {key}: {value}")
    
    print(f"\n{'='*80}")
    print("TOP 10 FAMILIES PER IDENTITY/ATTRIBUTE")
    print("="*80)
    
    for identity, data in sorted(results['identities'].items()):
        print(f"\n{identity.upper().replace('_', ' ')} ({data.get('geography', 'Unknown')}):")
        for family, count in list(data['counts'].items())[:10]:
            print(f"  {family:<20} ({count} mentions)")

