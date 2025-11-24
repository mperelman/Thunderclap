from query import get_engine
from lib.term_utils import canonicalize_term
import re
question='Tell me about Morgan banking in London'
stop_words={'the','a','an','and','or','but','in','on','at','to','for','of','with','by','from','about','what','when','where','who','why','how','did','do','does','was','were','is','are','tell','me'}
raw_tokens=re.findall(r"[A-Za-z']+", question)
keywords=[]
canonical_map={}
base=0
for token in raw_tokens:
    lower=token.lower()
    if lower in stop_words or len(lower)<=3:
        continue
    base+=1
    if token.isupper():
        keywords.append(token)
        continue
    canonical=canonicalize_term(token)
    if canonical:
        keywords.append(canonical)
        canonical_map.setdefault(canonical,set()).add(lower)
engine=get_engine()
subject_terms, subject_phrases=engine._extract_subject_filters(question, keywords, raw_tokens, canonical_map)
print('keywords', keywords)
print('subject_terms', subject_terms)
print('subject_phrases', subject_phrases)
