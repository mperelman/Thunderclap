from typing import List, Tuple


class IdeologyEngine:
    """
    Thin adapter around the monolithic engine for ideology topics (Marxism, Socialism, Communism, Collectivism).
    """
    def __init__(self, core_engine):
        self.core = core_engine

    def is_match(self, question: str) -> bool:
        return self.core._is_ideology_query(question)

    def generate(self, question: str, chunks: List[Tuple[str, dict]]) -> str:
        # Filter and sort using core helpers, then use the ideology prompt
        chunks = self.core._filter_chunks_for_ideology(chunks, question)
        try:
            chunks = self.core._sort_chunks_by_year(chunks)
            chunks = self.core._stratify_by_decade(chunks, cap_per_decade=5, max_total=60)
        except Exception:
            pass
        return self.core.llm.call_api(self.core._build_prompt_ideology(question, chunks))



