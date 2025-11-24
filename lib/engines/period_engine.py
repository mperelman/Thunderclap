from typing import List, Tuple, Optional


class PeriodEngine:
    """
    Adapter for broad topic queries using iterative period-based processing.
    """
    def __init__(self, core_engine):
        self.core = core_engine

    def is_match(self, question: str) -> bool:
        # Fallback engine for non-market/non-event/non-ideology queries
        return True

    def generate(
        self,
        question: str,
        chunks: List[Tuple[str, dict]],
        subject_terms: Optional[list] = None,
        subject_phrases: Optional[list] = None
    ) -> str:
        return self.core._generate_iterative_narrative(question, chunks, subject_terms, subject_phrases)



