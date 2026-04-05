"""
Shared constants for law/year prefix expansions and related mappings.
"""

YEAR_PREFIX_EXPANSIONS = {
    "BA": "Bankruptcy Act ",
    "TA": "Treasury Tax Act ",
    "SA": "Securities Act ",
    "FA": "Federal Reserve Act ",
    "IA": "Interstate Commerce Act ",
    "AA": "Antitrust Act ",
    "PA": "Public Utility Holding Company Act ",
    "DA": "Deposit Insurance Act ",
    "CA": "Clean Air/Climate Act ",
    "BHCA": "Bank Holding Company Act ",
    "EA": "Energy Act ",
    "LA": "Public mineral and land law "
}

LAW_YEAR_PREFIX_EXPANSIONS = {
    "BA": "Bankruptcy Act",
    "TA": "Treasury Tax Act",
    "SA": "Securities Act",
    "FA": "Federal Reserve Act",
    "IA": "Interstate Commerce Act",
    "AA": "Antitrust Act",
    "PA": "Public Utility Holding Company Act",
    "DA": "Deposit Insurance Act",
    "CA": "Clean Air/Climate Act",
    "BHCA": "Bank Holding Company Act",
    "EA": "Energy Act",
    "LA": "Public mineral and land law",
}

# Stop words for filtering terms/queries
# Used across multiple modules to avoid duplication
STOP_WORDS = {
    # Common stop words
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were',
    # Query words
    'tell', 'me', 'about', 'what', 'who', 'when', 'where', 'how', 'why',
    # Short words (typically filtered)
    'it', 'he', 'she', 'we', 'they', 'this', 'that', 'these', 'those',
    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
}

# Generic words that should NEVER be indexed
# These are excluded at indexing time - if they appear in the index, it's a bug
GENERIC_WORDS_TO_EXCLUDE = {
    # Common function words
    'and', 'or', 'but', 'the', 'a', 'an', 'of', 'to', 'in', 'on', 'at', 'by', 'for', 'with', 'from',
    'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
    # Family/relationship words
    'family', 'families', 'cousin', 'cousins', 'son', 'sons', 'daughter', 'daughters',
    'father', 'fathers', 'mother', 'mothers', 'brother', 'brothers', 'sister', 'sisters',
    'uncle', 'uncles', 'aunt', 'aunts', 'nephew', 'nephews', 'niece', 'nieces',
    'grandfather', 'grandmother', 'grandson', 'granddaughter',
    'husband', 'husbands', 'wife', 'wives', 'spouse', 'spouses', 'widow', 'widows', 'widower', 'widowers',
    # Ordinal/generic descriptors
    'first', 'second', 'third', 'last', 'next', 'previous', 'another', 'other', 'others',
    # Generic banking/finance words (standalone)
    'bank', 'banks', 'banking', 'employee', 'employees', 'worker', 'workers', 'staff', 'member', 'members',
    'financial', 'finance', 'financing', 'credit', 'credits', 'capital', 'securities', 'assets',
    'officials', 'official', 'policy', 'policies', 'funded', 'funding', 'fund', 'funds',
    'affairs', 'affair',  # Generic word (e.g., "Ministry of Internal Affairs" - don't index "affairs" standalone)
    'chief', 'rabbi', 'rabbis', 'chief rabbi',  # Generic titles (don't index standalone)
    # Generic descriptive words
    'political', 'politics', 'economic', 'economy', 'commercial', 'trade', 'trading', 'commerce',
    'war', 'wars', 'conflict', 'conflicts', 'battle', 'battles',
    'silver', 'gold', 'steel', 'iron', 'metal', 'metals', 'ship', 'ships', 'vessel', 'vessels',
    'oil', 'oils', 'rival', 'rivals', 'orient', 'gained', 'gain', 'gains',
    'american', 'america', 'british', 'french', 'german', 'european', 'asian', 'african',
    'cities', 'city', 'town', 'towns', 'place', 'places', 'region', 'regions',
    # Directional/geographic generic words (when standalone)
    'north', 'south', 'east', 'west', 'northern', 'southern', 'eastern', 'western',
    # Generic descriptive/occupational words
    'tech', 'technology', 'labor', 'labour', 'work', 'works', 'department', 'departments',
    # Generic titles/roles (standalone)
    'director', 'directors', 'president', 'presidents', 'chairman', 'chairmen', 'governor', 'governors',
    'minister', 'ministers', 'secretary', 'secretaries', 'manager', 'managers', 'officer', 'officers',
    # Common first names (should not be indexed as middle names or surnames)
    'joseph', 'john', 'william', 'james', 'robert', 'thomas', 'david', 'richard', 'charles', 'daniel',
    'matthew', 'anthony', 'mark', 'donald', 'paul', 'steven', 'andrew', 'kenneth', 'joshua', 'kevin',
    'brian', 'george', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan', 'jacob', 'gary',
    'nicholas', 'eric', 'stephen', 'jonathan', 'larry', 'justin', 'scott', 'brandon', 'benjamin', 'samuel',
    'frank', 'gregory', 'raymond', 'alexander', 'patrick', 'jack', 'dennis', 'jerry', 'tyler', 'aaron',
    'jose', 'henry', 'adam', 'douglas', 'nathan', 'zachary', 'kyle', 'noah', 'ethan', 'jeremy',
    'walter', 'christian', 'terry', 'sean', 'lawrence', 'juan', 'mason', 'roy', 'ralph', 'roger',
    'eugene', 'wayne', 'arthur', 'louis', 'peter', 'harold', 'carl', 'alan', 'harry', 'randy', 'albert',
    'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica', 'sarah', 'karen',
    'nancy', 'lisa', 'betty', 'margaret', 'sandra', 'ashley', 'kimberly', 'emily', 'donna', 'michelle',
    'dorothy', 'carol', 'amanda', 'melissa', 'deborah', 'stephanie', 'rebecca', 'sharon', 'laura', 'cynthia',
    'kathleen', 'amy', 'angela', 'shirley', 'anna', 'brenda', 'pamela', 'emma', 'nicole', 'virginia',
    'catherine', 'christine', 'samantha', 'debra', 'rachel', 'carolyn', 'janet', 'maria', 'heather',
    # Words that must not be hyperlinked (only proper/indexed terms should link)
    'following', 'competition', 'business', 'networks', 'into', 'largest', 'founded', 'their',
    'decree', 'money', 'since', 'after', 'left', 'became', 'between', 'which', 'service', 'sold',
    'partner', 'partners', 'acquired', 'during', 'through', 'under', 'over', 'same', 'such',
    'initiated', 'held', 'positions', 'position', 'managed', 'manage', 'manages', 'chair', 'control',
    'controls', 'controlled', 'controlling', 'enterprise', 'enterprises', 'leadership', 'involved',
}

# Generic words that are NOT surnames (used when extracting proper names)
GENERIC_NOT_SURNAMES = {
    'bank', 'banks', 'trust', 'trusts', 'company', 'companies', 'co', 'corp', 'corporation',
    'inc', 'incorporated', 'ltd', 'limited', 'group', 'holding', 'holdings',
    'partners', 'partnership', 'associates', 'brothers', 'sons', 'son',
    'york', 'london', 'paris', 'berlin', 'vienna', 'amsterdam', 'brussels', 'geneva',
    'america', 'american', 'british', 'french', 'german', 'swiss', 'italian',
    'national', 'international', 'federal', 'state', 'central', 'commercial',
    'investment', 'merchant', 'private', 'public', 'royal', 'imperial',
    'exchange', 'credit', 'finance', 'capital', 'securities', 'assets',
    # Also include family/relationship words
    'family', 'families', 'cousin', 'cousins', 'son', 'sons', 'daughter', 'daughters',
    'father', 'fathers', 'mother', 'mothers', 'brother', 'brothers', 'sister', 'sisters',
    'employee', 'employees', 'worker', 'workers', 'staff', 'member', 'members',
}

# Common first names - should NOT be indexed as middle names or surnames
COMMON_FIRST_NAMES = {
    'joseph', 'john', 'william', 'james', 'robert', 'thomas', 'david', 'richard', 'charles', 'daniel',
    # Biblical/religious names that are too common
    'abraham', 'isaac', 'jacob', 'moses', 'solomon', 'samuel', 'esther', 'ruth', 'hannah', 'anna',
    'matthew', 'anthony', 'mark', 'donald', 'paul', 'steven', 'andrew', 'kenneth', 'joshua', 'kevin',
    'brian', 'george', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan', 'jacob', 'gary',
    'nicholas', 'eric', 'stephen', 'jonathan', 'larry', 'justin', 'scott', 'brandon', 'benjamin', 'samuel',
    'frank', 'gregory', 'raymond', 'alexander', 'patrick', 'jack', 'dennis', 'jerry', 'tyler', 'aaron',
    'jose', 'henry', 'adam', 'douglas', 'nathan', 'zachary', 'kyle', 'noah', 'ethan', 'jeremy',
    'walter', 'christian', 'terry', 'sean', 'lawrence', 'juan', 'mason', 'roy', 'ralph', 'roger',
    'eugene', 'wayne', 'arthur', 'louis', 'peter', 'harold', 'carl', 'alan', 'harry', 'randy', 'albert',
    'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica', 'sarah', 'karen',
    'nancy', 'lisa', 'betty', 'margaret', 'sandra', 'ashley', 'kimberly', 'emily', 'donna', 'michelle',
    'dorothy', 'carol', 'amanda', 'melissa', 'deborah', 'stephanie', 'rebecca', 'sharon', 'laura', 'cynthia',
    'kathleen', 'amy', 'angela', 'shirley', 'anna', 'brenda', 'pamela', 'emma', 'nicole', 'virginia',
    'catherine', 'christine', 'samantha', 'debra', 'rachel', 'carolyn', 'janet', 'maria', 'heather',
    # Common verbs/words that create bad hyperlinks in answers
    'service', 'their', 'sold', 'opened', 'between', 'manage', 'became', 'into', 'competition', 'formed',
    'chair', 'vice', 'founded', 'moved', 'overseas', 'legal', 'also', 'controlled', 'world', 'expanded',
    'built', 'former', 'shares', 'after', 'hunter', 'partner', 'which', 'granted', 'they', 'money', 'mass',
    'coast', 'started', 'remittances', 'acquired', 'it', 'its', 'them', 'then', 'there', 'these', 'those',
}

# Terms that must NEVER appear as "related surnames" for an identity (autofill / GAY etc.)
# Place names, common words, or identity words wrongly tagged by the detector.
RELATED_SURNAMES_BLOCKLIST = {
    'indian', 'india', 'france', 'guard', 'exeter', 'foundation', 'party', 'fellow',
    'partners', 'post', 'carolina', 'york', 'general', 'romanovs',
}

# Multi-word generic phrases that should be excluded
GENERIC_PHRASES_TO_EXCLUDE = {
    'american cities', 'american city', 'british cities', 'european cities',
    'financial markets', 'financial market', 'political system',
    'chamber of commerce', 'board of directors', 'president of', 'director of',
    'acquired it',
}

# Extra tokens to never hyperlink in the browser when they appear as standalone index entries
# (answer prose / common given names). Single place for client; see hyperlink_skip_words_for_client().
HYPERLINK_SUPPLEMENTAL_WORDS = {
    'era', 'also', 'building', 'they', 'their', 'expanded', 'multiple', 'following',
    'concurrent', 'concurrently', 'amid', 'navigated', 'reflects', 'engagement', 'turbulent',
    'landscape', 'originating', 'developed', 'significant', 'unrest', 'pogroms',
    'period', 'events', 'international', 'earlier', 'later', 'directly', 'including',
    'while', 'although', 'however', 'therefore', 'related', 'questions',
    'asher',
}

_HYPERLINK_SKIP_WORDS_CACHE = None


def hyperlink_skip_words_for_client():
    """Lowercased tokens the UI must not auto-link; used by GET /terms (single source of truth)."""
    global _HYPERLINK_SKIP_WORDS_CACHE
    if _HYPERLINK_SKIP_WORDS_CACHE is not None:
        return _HYPERLINK_SKIP_WORDS_CACHE
    combined = set()
    combined.update(w.lower() for w in GENERIC_WORDS_TO_EXCLUDE)
    combined.update(w.lower() for w in GENERIC_PHRASES_TO_EXCLUDE)
    combined.update(w.lower() for w in COMMON_FIRST_NAMES)
    combined.update(w.lower() for w in HYPERLINK_SUPPLEMENTAL_WORDS)
    _HYPERLINK_SKIP_WORDS_CACHE = sorted(combined)
    return _HYPERLINK_SKIP_WORDS_CACHE


