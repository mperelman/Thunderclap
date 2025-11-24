"""Review the answer directly without API call."""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.answer_reviewer import AnswerReviewer

# The answer from the query
answer = """The Rothschild banking family established a branch in Vienna, Austria, becoming deeply embedded in the Austrian financial landscape through strategic investments and kinship networks, despite facing antisemitism.

**Early 19th Century: Establishing a Foothold**

Antisemitism in Vienna required Solomon Rothschild to seek permission from Metternich for his cousin Anton Schnapper to move to Vienna. By 1823, Schnapper married Maria Wertheim, a Katz-cousin descendant of Samson Wertheim. After Anton's brother married Maria's second cousin in 1829, Rothschild sought renewal of toleration for Moritz Goldschmidt, another Frankfurt-born cousin and employee. The Emperor ennobled Goldschmidt, Wertheim, and Schnapper between 1862 and 1865. Austria commissioned Rothschild Naples to fund the invasion and occupation of Southern Italy in 1822 and then ennobled the family. By 1829, Michael Daniel, a prominent Jewish moneylender in Moldova, had established financial ties with Rothschild in Frankfurt, Paris, and London. In 1823, the British government raised concerns about loans granted to Austria, and Metternich requested Solomon Rothschild to seek assistance from his brother, Nathan, to influence the British Ministry. Rothschild London enlisted Baring and Reid Irving to convince the London cabinet to reduce its claims in exchange for cash.

**1830s-1840s: Expansion and Investment**

Rothschild Vienna provided financial assistance to the Papacy during a period of turbulence in Italy. Ida Morpurgo married Ignacio Bauer, the nephew of Rothschild Vienna's chief clerk, Moritz Goldschmidt. Generali started in Trieste in 1831 with capital from Giuseppe Morpurgo, Marco Parente, Vidal Cusin, Samuel Vida, Bassevi, Luzzatto, and Rothschild Vienna. Rothschild Vienna invested in coal exploration in Istria and Dalmatia, opening Viennese Dalmatiam Coal Works in 1834. In 1836, Solomon Rothschild linked Vienna to the Adriatic. When Austrian Lloyd and Trieste insurers faced a crisis during the Panic of 1839, Carlo Bruck secured a loan from Rothschild Vienna. In 1840, David Gutmann convinced Rothschild Vienna to invest in coal mining in Ostrava, Moravia. Rothschild Vienna also provided financial assistance to the Papacy, financing Austrian military occupation from Ferrara to Bologna. In 1844, the family formed Rothschild Naples, but relied on agents like Parodi, Leonino, and Avigdor in Piedmont. Amidst the Panic of 1841, Rothschild Vienna took over former shared operations with Geymüller in Austrian Bohemia after Geymüller's bankruptcy. In 1845, Solomon Rothschild sought imperial support to overcome clergy opposition to their coal and asphalt operations in Dalmatia.

**1850s-1860s: Competition and Consolidation**

In 1855, Solomon Rothschild of Rothschild Vienna died. Mobilier rushed into Austria, and Mobilier-affiliated Arnstein Eskeles, Sina, and Count François Zichy built a railway into the Austrian frontier, joining Huguenots to start ORIENT RR in 1855. Crédit Mobilier bid on ORIENT RR, but Rothschild Vienna monopolized credit into Creditanstalt, with directors including Goldschmidt, Wertheim, Königswarter, Oppenheim, Haber, and Lämel in-laws, as well as Austrian princes Fürstenberg, Schwarzenberg and Auersperg. Amidst the riots of 1848 in Vienna, Salomon Rothschild fled the city. Rothschild Vienna financed Austria to suppress revolts from Austrian Milan to Piedmont. Rothschild Vienna would come to own a quarter of the large properties in Bohemia, along with their railroad properties across the empire. In 1855, Austria offered the concession to extend the railway towards Galician Lemberg to Rothschild Vienna's group, but they declined due to financial conflicts with Crédit Mobilier. By 1857, Rothschild established Bank of Commerce & Industry of Turin in Piedmont. By 1862, Rothschild, Royal Bank of Würtemberg, and Gunzburg collaborated on managing the Russian state loan. Having closed Rothschild Naples in 1863, Rothschild hired Schott Weill's uncle to manage her Naples office from 1867. In 1864, Rothschild Vienna's Julius Blum opened offices in Egypt and Trieste. In 1865, Austria faced a financial crisis, and the Austrian government turned to Rothschild and Baring for a loan. Anglo-Austrian Bank, Rothschild Vienna, and Haber promoted an extension of Austrian RR and related rails from Galicia to Croatia and Transylvania, listing shares on the German and British exchanges, with a state profit guarantee."""

print("="*70)
print("REVIEWING ANSWER")
print("="*70)

reviewer = AnswerReviewer()
results = reviewer.review(answer, chunks=None)
reviewer.print_report(results, answer)

# Extract years
years = set()
for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
    years.add(int(match.group(1)))
if years:
    print(f"\nTime frame: {min(years)} - {max(years)}")
    print(f"Latest year: {max(years)}")
    if max(years) < 1900:
        print(f"⚠️  WARNING: Answer stops at {max(years)}, but should cover 1900+")


