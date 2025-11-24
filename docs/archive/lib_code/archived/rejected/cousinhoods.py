"""
Banking Family Identity & Attribute Data - Centralized definitions.
Combines hardcoded expert knowledge with dynamically detected identities/attributes.
Goal: Improve detector over time to reduce/eliminate hardcoding.

NOTE: "Cousinhood" refers to small intermarried elite families (actual cousins/in-laws 
through repeated kinlinks), whereas this data structure contains broader identity/attribute 
categories (religion, ethnicity, gender, race) that apply to all members of a group.

IMPORTANT: Families can have MULTIPLE INDEPENDENT attributes - system is versatile.
A family should NOT have compound identities (e.g., NO "sephardi_court" attribute).
Instead, a family can have MULTIPLE SEPARATE attributes that coexist:

Example: Teixeira
  - Attribute 1: Sephardi (origin)
  - Attribute 2: Court Jew (role)
  - Attribute 3: Mennonite (conversion/association)
  - All three are independent, context determines which is relevant

Example: Hambro
  - Attribute 1: Jewish (origin)
  - Attribute 2: Converted
  - Attribute 3: London Cousinhood (kinlinks)

Example: Warburg
  - Attribute 1: Ashkenazi (current identity)
  - Attribute 2: Descended from Sephardi DelBanco (ancestry)

The detector captures these multiple attributes automatically through explicit_identities tracking.
Families appear in multiple cousinhood groups independently based on context in documents.
"""

import os
import json
from pathlib import Path

# Hardcoded cousinhoods (expert knowledge - to be reduced as detector improves)
# Note: Same family can appear in MULTIPLE cousinhoods with different attributes
# Example: Teixeira appears in jewish_sephardim AND jewish_court AND mennonite (3 separate entries)
# This allows versatile search: "sephardi" finds Teixeira, "court jew" finds Teixeira, "mennonite" finds Teixeira
HARDCODED_COUSINHOODS = {
    'jewish_sephardim': {
        'families': ['Abrabanel', 'Seneor', '*Mendes*', '*Sassoon*', 'DelBanco', 'Henriques', 'Teixeira (converted)'],
        'geography': 'expelled Spain/Portugal -> Amsterdam, Ottoman Empire'
    },
    'jewish_ashkenazim': {
        'families': ['*Rothschild*', '*Kuhn Loeb*', '*Seligman*', '*Lazard*', '*Warburg* (descended from Sephardim DelBanco)'],
        'geography': 'Poland/Germany, later kinlinked with Sephardim'
    },
    'jewish_court': {
        'families': ['Samuel *Oppenheim*', 'Samson Wertheimer', 'Teixeira (Sephardi, converted)'],
        'geography': 'Central Europe'
    },
    'quaker': {
        'families': ['*Barclay*', '*Lloyd*', '*Bevan*', '*Tritton*'],
        'geography': 'Britain/British colonies (incl. West Indies)/Pennsylvania'
    },
    'huguenot': {
        'families': ['*Hope* (Amsterdam)', '*Mallet* (Britain)', '*Thellusson* (Britain)'],
        'geography': 'spread from France'
    },
    'mennonite': {
        'families': ['Clercq', 'Fock', 'TenCate', 'Boissevain', 'Teixeira (also Sephardi Court Jew, converted)'],
        'geography': 'Holland/Dutch/Amsterdam/colonies'
    },
    'puritan': {
        'families': ['*Morgan*', '*Lee Higginson* (kinlinked with Boston Brahmin elite)'],
        'geography': 'New England/America'
    },
    'boston_brahmin': {
        'families': ['Cabot', 'Lowell', 'Forbes', 'Perkins'],
        'geography': 'Puritan elite subset, New England'
    },
    'knickerbocker': {
        'families': ['Patroons (Rensselaer)', 'Schuyler', 'Schaack', 'Roosevelt', 'Livingston'],
        'geography': 'New York'
    },
    'protestant_cologne': {
        'families': ['*Stein*', '*Schaaffhausen* (German, kinlinked with Jewish *Oppenheim*)'],
        'geography': 'German (Cologne region)'
    },
    'greek_orthodox': {
        'families': ['Byzantine/Ottoman connections'],
        'geography': 'Byzantine, Ottoman Empire'
    },
    'armenian': {
        'families': ['Balian', 'Dadian', 'Gulbenkian'],
        'geography': 'Ottoman Empire'
    },
    'parsee': {
        'families': ['Tata', 'Wadia', 'Petit'],
        'geography': 'India, Zoroastrian'
    },
    'overseas_chinese': {
        'families': ['Wang-lee', 'Lamsam', 'Chen Sophonpanich', 'Salim', 'Riady'],
        'geography': 'Southeast Asia (Thailand, Indonesia, Hong Kong) - Christian or Buddhist, context-dependent'
    },
    'korean_chaebol': {
        'families': ['Samsung (Lee Byung-chul)', 'LG (Koo Cha-kyung)', 'Hyundai (Chung Ju-yung)'],
        'geography': 'Korea - family conglomerates, Christian or Buddhist'
    },
    'japanese_zaibatsu': {
        'families': ['[To be discovered by detector]'],
        'geography': 'Japan - family conglomerates, dissolved post-WWII'
    }
}

# Cross-group kinlinks (fundamental pattern)
# Note: Families can have MULTIPLE identities and act as bridges between cousinhoods
KINLINKS = [
    "*Schroder*/*Baring* (Germanic Protestant) kinlinked with London cousinhood (Anglican Smyth, converted Jewish *Hambro*, Cobbold)",
    "*Oppenheim* (Jewish) kinlinked with Protestant Cologne (*Stein*, *Schaaffhausen*)",
    "Greeks married Huguenots; *Morgan* kinlinked with Boston Brahmin",
    "Cross-group networks were essential to banking access and power"
]


def format_cousinhood_examples() -> str:
    """
    Format cousinhood examples for inclusion in prompts.
    
    Returns:
        Formatted string with all cousinhood examples
    """
    lines = []
    
    # Jewish subgroups
    lines.append(f"  * Jewish - Sephardim: {', '.join(COUSINHOODS['jewish_sephardim']['families'])} ({COUSINHOODS['jewish_sephardim']['geography']})")
    lines.append(f"  * Jewish - Ashkenazim: {', '.join(COUSINHOODS['jewish_ashkenazim']['families'])} ({COUSINHOODS['jewish_ashkenazim']['geography']})")
    lines.append(f"  * Jewish - Court Jews: {', '.join(COUSINHOODS['jewish_court']['families'])}")
    
    # Other cousinhoods
    for key in ['quaker', 'huguenot', 'mennonite', 'puritan', 'boston_brahmin', 'knickerbocker', 
                'protestant_cologne', 'greek_orthodox', 'armenian', 'parsee']:
        name = key.replace('_', ' ').title()
        families = ', '.join(COUSINHOODS[key]['families'])
        geography = COUSINHOODS[key]['geography']
        lines.append(f"  * {name}: {families} ({geography})")
    
    return "\n".join(lines)


def format_kinlinks() -> str:
    """
    Format cross-group kinlink examples.
    
    Returns:
        Formatted string with kinlink examples
    """
    return "\n  * " + "\n  * ".join(KINLINKS)


def load_detected_identities():
    """
    Load dynamically detected identities/attributes from detector cache.
    Returns empty dict if no detection has been run yet.
    
    File: data/detected_identities.json
    """
    try:
        # Get project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        cache_file = project_root / 'data' / 'detected_identities.json'
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def merge_cousinhoods():
    """
    Merge hardcoded cousinhoods with detected ones.
    Hardcoded takes priority, detected supplements.
    
    Returns:
        Combined cousinhoods dictionary
    """
    detected = load_detected_identities()
    merged = {}
    
    # Start with hardcoded (expert knowledge)
    for key, data in HARDCODED_COUSINHOODS.items():
        merged[key] = {
            'families': data['families'].copy(),
            'geography': data['geography'],
            'source': 'hardcoded'
        }
    
    # Add detected families that aren't in hardcoded
    for detected_key, detected_data in detected.get('cousinhoods', {}).items():
        # Map detected keys to hardcoded keys
        key_mapping = {
            'sephardim': 'jewish_sephardim',
            'ashkenazim': 'jewish_ashkenazim',
            'court_jew': 'jewish_court',
            'quaker': 'quaker',
            'huguenot': 'huguenot',
            'mennonite': 'mennonite',
            'boston_brahmin': 'boston_brahmin',
            'parsee': 'parsee',
            'armenian': 'armenian'
        }
        
        hardcoded_key = key_mapping.get(detected_key)
        if hardcoded_key and hardcoded_key in merged:
            # Extract just surnames from hardcoded for comparison
            hardcoded_surnames = set()
            for fam in merged[hardcoded_key]['families']:
                clean = fam.replace('*', '').split('(')[0].strip().split()[-1].lower()
                hardcoded_surnames.add(clean)
            
            # Add detected families not in hardcoded
            detected_families = detected_data.get('families', [])[:10]  # Top 10
            for det_fam in detected_families:
                if det_fam.lower() not in hardcoded_surnames:
                    # Add with note that it's detected
                    merged[hardcoded_key]['families'].append(f"{det_fam.capitalize()} [detected]")
    
    return merged


# Combined cousinhoods (hardcoded + detected)
COUSINHOODS = merge_cousinhoods()

