"""Test LGBT detection on user-provided passage"""
import re

passage = """
Among these crises, AIDS silently ravaged America's gay community. Like Jews that left their religion or practiced in secret, even elite LGBT did not feel comfortable about fully acknowledging themselves publicly. As Donaldson Lufkin Jenrette's co-founder Richard Jenrette concealed his long-term relationship with William Thompson for decades amidst a culture of homophobia, DBL's Leon Lambert remained closeted, even after he died from AIDS-related complications in 1987. ...After earning a computer science MS from Harvard and PhD in medical information from Stanford, New Mexico-born Martin Chavez was Global Head of Energy Derivatives at CSFB from 1997 until Enron collapsed. The technologist then automated Goldman as Global Co-Head of Securities, CIO, and CFO. He also served as a Harvard Overseer. While tracing his Sephardi ancestry to gain Spanish citizenship and praising his single mother of Basque and Aztec descent, he identified as Hispanic and gay. (Likewise, Martin's siblings graduated Harvard and Stanford, became entrepreneurs, and identified mostly with their Hispanic heritage.)  

Mixed identities also helped Kamala Harris, the daughter of an Indian Brahmin mother and Jamaican-born Marxist taught economics at Stanford. Serving as the District Attorney of San Francisco from 2004, she succeeded Jerry Brown as Attorney General in 2011 and Barbara Boxer as Senator from California from 2017. 

Along with gays themselves, straight executives' views shifted from personal connections. After their children came out as gay, John Mack, former CEOs of Morgan Stanley and CSFB, Paul Singer, CEO of hedge fund Elliott Management, and Dan O'Connell, CEO of private equity Vestar Capital Partners, experienced significant transformations in their perspectives on LGBTQ issues. Initially holding anti-gay or indifferent views, Mack, Singer, and O'Connell became vocal advocates for LGBTQ rights, aligning with more inclusive policies. Mack's son came out in 1997, Singer's in 1998, and O'Connell's in 2011. These personal experiences led them to support equality initiatives. Singer notably pushed the Republican Party to back gay rights, launching American Unity PAC in 2012. By 2015, gay marriage became legal nationally. .. Meanwhile, as four Black Congressmen called on Yellen for identity diversity in 2017, Obama's housing policy official Raphael Bostic became the first Black and openly gay person to lead a regional FRS bank when he was appointed as the president of FRS Atlanta. The following year, Mary Daly, who had been with FRS San Francisco since 1996, became the first openly gay woman to lead a regional FRS bank. .. In his pursuit of a historically diverse Cabinet, Biden appointed Katherine Tai, the daughter of Taiwanese immigrants, the first non-White woman to represent American trade, and Department of Transportation's Pete Buttigieg as the first open gay (with a stint at McKinsey).... In France, Gabriel Attal became France's youngest PM at 34 and the country's first openly gay leader in early 2024.
"""

# LGBT individuals explicitly mentioned:
lgbt_people = [
    ("Richard Jenrette", "concealed his long-term relationship"),
    ("Leon Lambert", "remained closeted, died from AIDS"),
    ("Martin Chavez", "identified as Hispanic and gay"),
    ("Raphael Bostic", "first Black and openly gay person"),
    ("Mary Daly", "first openly gay woman"),
    ("Pete Buttigieg", "first open gay"),
    ("Gabriel Attal", "first openly gay leader"),
]

print("LGBT INDIVIDUALS MENTIONED IN PASSAGE:")
print("="*60)
for name, context in lgbt_people:
    print(f"\n{name}")
    print(f"  Context: {context}")

# Test current patterns
patterns = {
    'Pattern 1': r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+became\s+the\s+first.{0,50}?openly\s+(?:gay|lesbian)',
    'Pattern 2': r'first\s+openly\s+(?:gay|lesbian).{0,80}?to\s+lead.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'Pattern 4': r'first\s+openly\s+(?:gay|lesbian)\s+(?:woman|man|person).{0,50}?to\s+lead.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'Pattern 5': r'first\s+Black\s+and\s+openly\s+(?:gay|lesbian)\s+person.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'Pattern 6': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}openly\s+bisexual',
    'Pattern 7': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}(?:gay|lesbian)\s+social\s+circles',
    'Pattern 8': r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:concealed|remained closeted)',
    'Pattern 9': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}identified\s+as.{0,30}(?:gay|lesbian|bisexual)',
    'Pattern 10': r'first\s+openly\s+(?:gay|lesbian)\s+woman.{0,50}?\b([A-Z][a-z]+\s+[A-Z][a-z]+)',
    'Pattern 11': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}first\s+open\s+gay',
    'Pattern 12': r'([A-Z][a-z]+\s+[A-Z][a-z]+).{0,50}died\s+from\s+AIDS',
}

print("\n" + "="*60)
print("TESTING PATTERNS:")
print("="*60)

for pattern_name, pattern in patterns.items():
    matches = re.findall(pattern, passage)
    if matches:
        print(f"\n{pattern_name}: {matches}")

