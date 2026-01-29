"""
Test that Cunliffe (and similar single-term queries) never return unrelated passages.
- sanitize_final_answer: if answer doesn't contain query term, return fallback.
- _filter_chunks_by_question_terms: chunks without query term are filtered out.
"""
import re
import sys
import os

# Add project root so we can import lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.constants import STOP_WORDS


def _extract_terms(question: str):
    """Same logic as _filter_chunks_by_question_terms."""
    tokens = re.findall(r"[A-Za-z']+", question)
    return [t.lower() for t in tokens if t.lower() not in STOP_WORDS and len(t) > 3]


def _answer_contains_query_term(question: str, answer: str) -> bool:
    """Same logic as sanitize_final_answer: whole-word match of any question term in answer."""
    terms = _extract_terms(question)
    if not terms:
        return True
    answer_lower = answer.lower()
    for term in terms:
        if re.search(rf'\b{re.escape(term)}\b', answer_lower):
            return True
    return False


def test_sanitizer_logic():
    """Test that unrelated long answer for 'Cunliffe' would be replaced by fallback."""
    question = "Cunliffe"
    # The kind of unrelated answer the user gets (excerpt)
    unrelated = (
        "Found 9 relevant passages:\n\n"
        "[Thunderclap Part II.docx] New York, and Madrid. As in Britain, the French Court Jew system "
        "faced a reckoning. Morgan's Henry Davison negotiating with Parisienne's Octave Homberg. "
        "Negotiating French foreign debts with Mendelssohn Amsterdam's Mannheimer, Reynaud cousin Paul Reynaud."
    )
    assert not _answer_contains_query_term(question, unrelated), (
        "Unrelated answer must NOT contain 'Cunliffe' so sanitizer would replace it"
    )
    # Answer that does mention Cunliffe should be kept
    related = "Lord Cunliffe was Governor of the Bank of England during WWI."
    assert _answer_contains_query_term(question, related), (
        "Related answer containing 'Cunliffe' must be kept"
    )
    # Short question term extraction
    assert _extract_terms("Cunliffe") == ["cunliffe"], "Single term 'Cunliffe' should be extracted"
    assert "cunliffe" in _extract_terms("Lord Cunliffe"), "Query term 'Cunliffe' must be in terms"
    # Call actual module-level sanitizer (used by server)
    from lib.query_engine import sanitize_final_answer_for_question
    replaced = sanitize_final_answer_for_question("Cunliffe", unrelated)
    assert "Cunliffe" not in replaced and "search term" in replaced, "Unrelated answer must be replaced by fallback"
    kept = sanitize_final_answer_for_question("Cunliffe", related)
    assert kept == related, "Related answer must be kept"
    # Body-only check: "Found 9 relevant passages:" with body that has no Cunliffe -> replaced
    found_style = "Found 9 relevant passages:\n\n[Doc] Morgan and Homberg. French debt. Mendelssohn Amsterdam."
    replaced2 = sanitize_final_answer_for_question("Cunliffe", found_style)
    assert "search term" in replaced2, "Found N passages with unrelated body must be replaced"
    # Body that does contain Cunliffe -> kept
    found_style_ok = "Found 1 relevant passages:\n\n[Doc] Lord Cunliffe was Governor of the Bank of England."
    kept2 = sanitize_final_answer_for_question("Cunliffe", found_style_ok)
    assert kept2 == found_style_ok, "Found N passages with body containing term must be kept"
    print("test_sanitizer_logic: OK")


def test_filter_chunks():
    """Test that chunks without query term are filtered out."""
    terms = _extract_terms("Cunliffe")
    assert terms == ["cunliffe"]
    # Chunk with Cunliffe: keep
    text_with = "Lord Cunliffe served as Governor of the Bank of England."
    text_with_lower = text_with.lower()
    kept = any(re.search(rf'\b{re.escape(t)}\b', text_with_lower) for t in terms)
    assert kept, "Chunk containing 'Cunliffe' should be kept"
    # Chunk without Cunliffe: drop
    text_without = "Morgan's Henry Davison negotiated with Parisienne's Octave Homberg."
    text_without_lower = text_without.lower()
    kept_no = any(re.search(rf'\b{re.escape(t)}\b', text_without_lower) for t in terms)
    assert not kept_no, "Chunk without 'Cunliffe' should be dropped"
    print("test_filter_chunks: OK")


if __name__ == "__main__":
    test_sanitizer_logic()
    test_filter_chunks()
    print("All tests passed.")
