"""Test LGBT detection on lavender marriages passage"""
import re

passage = """
Other times, from America to Europe, including the children of aristocrats, Drexel, Singer, and Barney (started by Jay Cooke's son-in-law), entered 'lavender' marriages with other homosexual heirs in often unconsummated marriages and engaged in extra-marital affairs with varying degrees of discretion.  Although sodomy had long been illegal in Britain, aristocratic homosexuals became more open in the 1890s. Since Marc Wertheim Rafalovich immigrated from Paris to London, he became romantically involved with John Gray, on whom their mutual friend Oscar Wilde based his fictional character Dorian Gray. When a homophobic campaign led many gays to flee to Paris in 1895, Rafalovich converted to Catholicism like his mother and sister, but remained involved with Gray until death in the 1930s.  

While the daughter of Morgan London's Burns married an aristocratic around whom rumors often swirled, another homophobic scandal alleged homosexual offenses by 30 upper-class men by 1902, included Cyril Flower and King Edward VII's brother-in-law, the Duke of Argyll. Since marrying Constance Rothschild, Cyril continued his father's development and engaged in politics. Only intervention by PM Balfour and King Edward prevented the case from proceeding, protecting Cyril and his associates from public exposure and consequences.

Robert Boothby—a son of a Royal Bank of Scotland director, grand-nephew of former BOE Governor Cunliffe, and a second cousin of a Baring—maintained a publicly heterosexual identity, navigating gay social circles with political caution while denying physical involvement.

Miriam Rothschild assembled a group of biologists and zoologists to submit a report on homosexuality and genetics. This report, though omitting her name, advocated against criminalizing private homosexual acts between consenting adults and highlighted the predominant genetic component. Despite its modest recommendations, including setting the age of consent at 21, these ideas eventually contributed to the 1967 decriminalization of homosexual behavior in Britain. Miriam's efforts were motivated by a desire to end the threat of blackmail against gay men, reflecting her own experiences as an openly bisexual woman in a homophobic society.
"""

# Test patterns (UPDATED to match identity_detector.py)
patterns = {
    'Pattern 13 (lavender)': r'([A-Z][a-z]+)(?=.{0,100}lavender\s+marriages)',
    'Pattern 14 (offenses)': r'homosexual\s+offenses.{0,100}included\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'Pattern 15 (romantically)': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}).{0,50}romantically\s+involved\s+with',
    'Pattern 16 (bisexual)': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,500}openly\s+bisexual\s+woman',
    'Pattern 17 (gay circles)': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,200}navigating\s+gay\s+social\s+circles',
}

print("TESTING NEW PATTERNS FOR LAVENDER MARRIAGES:")
print("="*60)

for pattern_name, pattern in patterns.items():
    matches = re.findall(pattern, passage)
    if matches:
        print(f"\n{pattern_name}:")
        for m in matches:
            print(f"  - {m}")
    else:
        print(f"\n{pattern_name}: NO MATCHES")

