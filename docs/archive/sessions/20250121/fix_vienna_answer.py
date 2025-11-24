"""Review and fix the Vienna Rothschild answer."""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.answer_reviewer import AnswerReviewer
from lib.query_engine import QueryEngine

# The answer to fix
answer = """Vienna Rothschild Banking Overview

The Rothschild banking family established a branch in Vienna, Austria, becoming deeply embedded in the Austrian financial landscape, shaped by sociological factors like their Jewish identity and kinship networks, and their involvement in major financial events.

Early 19th Century: Establishing a Foothold

Antisemitism in Vienna required Solomon Rothschild to seek permission from Metternich for his cousin Anton Schnapper to move to Vienna. By 1823, Schnapper married Maria Wertheim, connecting the Rothschilds to the Katz-cousin descendants of Samson Wertheim. After Anton's brother married Maria's second cousin in 1829, Rothschild sought toleration renewal for Moritz Goldschmidt, another Frankfurt-born cousin and employee. Austria commissioned Rothschild Naples to fund the invasion and occupation of Southern Italy in 1822 and then ennobled the family. In 1823, the British government raised concerns about loans granted to Austria, and Metternich requested Solomon Rothschild to seek assistance from his brother, Nathan, to influence the British Ministry. Rothschild London enlisted Baring and Reid Irving to convince the London cabinet to reduce its claims in exchange for cash. By 1829, Michael Daniel, a prominent Jewish moneylender in Moldova, had established financial ties with Rothschild in Frankfurt, Paris, and London.

Mid-19th Century: Expansion, Railways and Crises

The Panic of 1825 led to the failure of Austrian banker Fries without aid from Rothschild Vienna. Arnstein Eskeles took over Fries, and Fries descendants kinlinked with Arnstein Eskeles' ennobled converted descendants of Katz, Daniel Itzig-Jaffe, and Samson Wertheim. In the 1830s, Rothschild Vienna became involved in the insurance industry in Trieste, investing in Generali in 1831 and Lloyd Austria by 1833. Ida Morpurgo married Ignacio Bauer, the nephew of Rothschild Vienna's chief clerk, Moritz Goldschmidt. In 1840, David Gutmann convinced Rothschild Vienna to invest in coal mining in Ostrava, Moravia. Rothschild Vienna also provided financial assistance to the Papacy, financing Austrian military occupation from Ferrara to Bologna. In 1844, the family formed Rothschild Naples, but relied on agents like Parodi, Leonino, and Avigdor in Piedmont. By 1836, Solomon Rothschild linked Vienna to the Adriatic. Rothschild Vienna secured a concession for Austrian RR to connect Viennese markets, industrial Moravia and Silesia, and agricultural Galicia. When Austrian Lloyd faced a crisis during the Panic of 1839, Carlo Bruck secured a loan from Rothschild Vienna. Amidst the Panic of 1841, Rothschild Vienna took over former shared operations with Geymüller in Austrian Bohemia after Geymüller's bankruptcy. In 1845, Solomon Rothschild sought imperial support to overcome clergy opposition to their coal and asphalt operations in Dalmatia. In 1855, Solomon Rothschild of Rothschild Vienna died. Mobilier rushed into Austria, and Mobilier-affiliated Arnstein Eskeles, Sina, and Count François Zichy built a railway into the Austrian frontier, joining Huguenots to start ORIENT RR in 1855. Crédit Mobilier bid on ORIENT RR, but Rothschild Vienna monopolized credit into Creditanstalt, with directors including Goldschmidt, Wertheim, Königswarter, Oppenheim, Haber, and Lämel in-laws, as well as Austrian princes Fürstenberg, Schwarzenberg and Auersperg.

Late 19th Century: Revolutions, Competition and Consolidation

Amidst the riots of 1848 in Vienna, Salomon Rothschild fled the city. Rothschild Vienna financed Austria to suppress revolts from Austrian Milan to Piedmont. Rothschild Vienna would come to own a quarter of the large properties in Bohemia, along with their railroad properties across the empire. In 1855, Austria offered the concession to extend the railway towards Galician Lemberg to Rothschild Vienna's group, but they declined due to financial conflicts with Crédit Mobilier. By 1857, Rothschild established Bank of Commerce & Industry of Turin in Piedmont. By 1862, Rothschild, Royal Bank of Würtemberg, and Gunzburg collaborated on managing the Russian state loan. Having closed Rothschild Naples in 1863, Rothschild hired Schott Weill's uncle to manage her Naples office from 1867. In 1864, Rothschild Vienna's Julius Blum opened offices in Egypt and Trieste. In 1865, Austria faced a financial crisis, and the Austrian government turned to Rothschild and Baring for a loan. Anglo-Austrian Bank, Rothschild Vienna, and Haber promoted an extension of Austrian RR and related rails from Galicia to Croatia and Transylvania, listing shares on the German and British exchanges, with a state profit guarantee.

Kinship and Business Networks

The Rothschilds maintained a network through kinship and marriage. Anton Schnapper's marriage to Maria Wertheim in 1823 connected the Rothschilds to the Katz-cousin descendants of Samson Wertheim. Anton's brother wed Maria's second cousin in 1829. Rothschild Frankfurt, Rothschild Paris, Hirsch, Eichthal, and Bischoffsheim collaborated on Bavarian and German roads. Rothschild Vienna negotiated Lombard-Venetian & Central Italian RR with Creditanstalt."""

print("="*70)
print("ORIGINAL ANSWER REVIEW")
print("="*70)

# Initialize reviewer and engine
reviewer = AnswerReviewer()
engine = QueryEngine(use_async=False)

# Review the answer
results = reviewer.review(answer, chunks=None)
reviewer.print_report(results, answer)

# Extract years to see time frame
years = set()
for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
    years.add(int(match.group(1)))
if years:
    print(f"\nTime frame: {min(years)} - {max(years)}")
    print(f"Latest year: {max(years)}")

print("\n" + "="*70)
print("APPLYING FIXES")
print("="*70)

# Apply paragraph enforcement
fixed_answer = engine._enforce_paragraph_limit(answer, max_sentences=3)

print("\n" + "="*70)
print("FIXED ANSWER")
print("="*70)
print(fixed_answer)

print("\n" + "="*70)
print("FIXED ANSWER REVIEW")
print("="*70)

# Review the fixed answer
fixed_results = reviewer.review(fixed_answer, chunks=None)
reviewer.print_report(fixed_results, fixed_answer)

# Extract years from fixed answer
fixed_years = set()
for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', fixed_answer):
    fixed_years.add(int(match.group(1)))
if fixed_years:
    print(f"\nTime frame: {min(fixed_years)} - {max(fixed_years)}")
    print(f"Latest year: {max(fixed_years)}")


