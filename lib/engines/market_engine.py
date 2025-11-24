from typing import List, Tuple


class MarketEngine:
    """
    Thin adapter around the monolithic engine for market/asset queries.
    Intended as the future home for market-specific retrieval, prompting,
    and merging logic.
    """
    def __init__(self, core_engine):
        self.core = core_engine  # monolithic engine instance

    def is_match(self, question: str) -> bool:
        return self.core._is_market_query(question)  # reuse existing detection

    def generate(self, question: str, chunks: List[Tuple[str, dict]]) -> str:
        # Reuse existing geographic flow used for market queries
        try:
            chunks = self.core._sort_chunks_by_year(chunks)
        except Exception:
            pass
        return self.core._generate_geographic_narrative(question, chunks, for_market=True)



