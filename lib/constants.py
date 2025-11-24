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



