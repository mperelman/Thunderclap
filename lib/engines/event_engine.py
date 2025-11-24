from typing import List, Tuple


class EventEngine:
    """
    Adapter for event queries (panics, crises, wars).
    """
    def __init__(self, core_engine):
        self.core = core_engine

    def is_match(self, question: str) -> bool:
        return self.core._is_event_query(question)

    def generate(self, question: str, chunks: List[Tuple[str, dict]]) -> str:
        # Use the existing geographic/sector clustering for events
        return self.core._generate_geographic_narrative(question, chunks)



