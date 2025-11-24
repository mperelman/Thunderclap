"""Review an answer from the API against criteria."""
import sys
import os
import json
import re
import requests
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Import reviewer directly to avoid query_engine import issues
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Copy reviewer code here to avoid imports
@dataclass
class ReviewResult:
    criterion: str
    passed: bool
    score: float
    details: str
    issues: List[str]

class AnswerReviewer:
    def __init__(self):
        self.criteria = {
            'paragraph_length': self._check_paragraph_length,
            'chronological_flow': self._check_chronological_flow,
            'full_history': self._check_full_history,
        }
    
    def review(self, answer: str, chunks: Optional[List[Tuple[str, dict]]] = None) -> Dict[str, ReviewResult]:
        results = {}
        for criterion_name, check_func in self.criteria.items():
            try:
                result = check_func(answer, chunks)
                results[criterion_name] = result
            except Exception as e:
                results[criterion_name] = ReviewResult(
                    criterion=criterion_name,
                    passed=False,
                    score=0.0,
                    details=f"Error: {e}",
                    issues=[str(e)]
                )
        return results
    
    def _check_paragraph_length(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        issues = []
        paras = [p.strip() for p in re.split(r'\n\s*\n+', answer) if p.strip()]
        long_paras = []
        for i, para in enumerate(paras):
            if para.startswith('**') and '\n' not in para:
                continue
            sentences = self._count_sentences(para)
            if sentences > 3:
                long_paras.append((i+1, sentences))
                issues.append(f"Paragraph {i+1} has {sentences} sentences (max 3)")
        total_paras = len([p for p in paras if not (p.startswith('**') and '\n' not in p)])
        long_count = len(long_paras)
        if long_count == 0:
            return ReviewResult('paragraph_length', True, 1.0, f"All {total_paras} paragraphs ≤3 sentences", [])
        else:
            score = max(0.0, 1.0 - (long_count / max(total_paras, 1)) * 0.5)
            return ReviewResult('paragraph_length', False, score, f"{long_count}/{total_paras} paragraphs exceed 3 sentences", issues[:5])
    
    def _check_chronological_flow(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        issues = []
        years = []
        for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
            year = int(match.group(1))
            pos = match.start()
            years.append((year, pos))
        if len(years) < 2:
            return ReviewResult('chronological_flow', True, 1.0, "Insufficient years to check", [])
        backwards_jumps = []
        for i in range(len(years) - 1):
            current_year, current_pos = years[i]
            for j in range(i + 1, len(years)):
                later_year, later_pos = years[j]
                if current_year > later_year:
                    backwards_jumps.append((current_year, later_year))
                    issues.append(f"Year {current_year} mentioned after {later_year}")
        if not backwards_jumps:
            return ReviewResult('chronological_flow', True, 1.0, f"Flow maintained across {len(years)} years", [])
        else:
            score = max(0.0, 1.0 - (len(backwards_jumps) / len(years)) * 0.3)
            return ReviewResult('chronological_flow', False, score, f"{len(backwards_jumps)} backwards jumps", issues[:5])
    
    def _check_full_history(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        if not chunks:
            return ReviewResult('full_history', True, 1.0, "No chunks for comparison", [])
        chunk_years = set()
        for text, _ in chunks:
            matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            chunk_years.update(int(m) for m in matches)
        if not chunk_years:
            return ReviewResult('full_history', True, 1.0, "No years in chunks", [])
        chunk_latest = max(chunk_years)
        chunk_earliest = min(chunk_years)
        answer_years = set()
        for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
            answer_years.add(int(match.group(1)))
        if not answer_years:
            return ReviewResult('full_history', False, 0.0, f"No years in answer, chunks span {chunk_earliest}-{chunk_latest}", [f"Missing all coverage"])
        answer_latest = max(answer_years)
        answer_earliest = min(answer_years)
        gap = chunk_latest - answer_latest
        issues = []
        if gap > 20:
            issues.append(f"Stops at {answer_latest}, chunks go to {chunk_latest} (gap: {gap} years)")
        if chunk_latest >= 1900 and answer_latest < 1900:
            issues.append("Missing 20th century")
        if chunk_latest >= 2000 and answer_latest < 2000:
            issues.append("Missing 21st century")
        if not issues:
            return ReviewResult('full_history', True, 1.0, f"Full coverage: {answer_earliest}-{answer_latest} vs {chunk_earliest}-{chunk_latest}", [])
        else:
            score = max(0.0, 1.0 - (gap / 100.0)) if gap > 0 else 0.8
            return ReviewResult('full_history', False, score, f"Incomplete: {answer_earliest}-{answer_latest} vs {chunk_earliest}-{chunk_latest} (gap: {gap})", issues)
    
    def _count_sentences(self, text: str) -> int:
        sentences = re.split(r'[.!?]+\s+(?=[A-Z])', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) == 1:
            sentences = re.findall(r'[^.!?]*[.!?]+', text)
        return len(sentences) if sentences else 1
    
    def print_report(self, results: Dict[str, ReviewResult], answer: str = None):
        print("\n" + "="*70)
        print("ANSWER REVIEW REPORT")
        print("="*70)
        all_passed = all(r.passed for r in results.values())
        failures = []
        for criterion, result in results.items():
            if result.passed:
                print(f"\n[PASS] - {result.criterion.upper().replace('_', ' ')}")
                print(f"  {result.details}")
            else:
                print(f"\n[FAIL] - {result.criterion.upper().replace('_', ' ')}")
                print(f"  {result.details}")
                if result.issues:
                    print(f"  SPECIFIC FAILURES:")
                    for issue in result.issues:
                        print(f"    - {issue}")
                    failures.extend(result.issues)
        print("\n" + "="*70)
        if all_passed:
            print("OVERALL: ALL CRITERIA PASSED")
        else:
            print("OVERALL: FAILURES DETECTED")
            print("\nACTION REQUIRED - Fix these issues:")
            for i, failure in enumerate(failures, 1):
                print(f"  {i}. {failure}")
        print("="*70 + "\n")
        return all_passed, failures

def review_api_answer(question: str = None, use_saved: bool = False):
    """
    Review answer from API or from saved file.
    
    Args:
        question: Query to send to API (if not using saved)
        use_saved: If True, review from temp/last_answer.txt instead of API
    """
    answer = None
    
    if use_saved:
        # Try to read from consistent saved file
        saved_file = "temp/last_answer.txt"
        if os.path.exists(saved_file):
            print(f"Reading answer from {saved_file}...")
            with open(saved_file, 'r', encoding='utf-8') as f:
                answer = f.read()
            print(f"Answer length: {len(answer)} chars")
        else:
            print(f"Error: {saved_file} not found. Run a query first or use API mode.")
            return None
    else:
        if not question:
            print("Error: question required when not using saved file")
            return None
            
        print(f"Query: {question}")
        print("Fetching answer from API...")
        
        # Get answer from API
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": question, "max_length": 15000},
            timeout=600  # Increased to 10 minutes for complex queries
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        answer = data.get("answer", "")
        
        print(f"Answer length: {len(answer)} chars")
        
        # Save to consistent file for future review
        os.makedirs("temp", exist_ok=True)
        with open("temp/last_answer.txt", 'w', encoding='utf-8') as f:
            f.write(answer)
        print(f"Saved answer to temp/last_answer.txt for future review")
    
    # Get chunks for comparison
    chunks = None
    try:
        import chromadb
        # Try to find the collection
        chroma_client = chromadb.PersistentClient(path="vectordb")
        collections = chroma_client.list_collections()
        collection_name = None
        for col in collections:
            if "thunderclap" in col.name.lower() or "chunk" in col.name.lower():
                collection_name = col.name
                break
        if not collection_name and collections:
            collection_name = collections[0].name
        
        collection = None
        if collection_name:
            collection = chroma_client.get_collection(name=collection_name)
        
        if not collection:
            raise Exception("No collection found")
        
        # Extract keywords from question
        question_lower = question.lower()
        keywords = []
        if "vienna" in question_lower and "rothschild" in question_lower:
            keywords = ["vienna", "rothschild"]
        elif "vienna" in question_lower:
            keywords = ["vienna"]
        elif "rothschild" in question_lower:
            keywords = ["rothschild"]
        
        # Get chunks mentioning these terms
        if keywords:
            chunk_ids = set()
            # Try to get term indices (simplified - would need full query engine)
            # For now, search by metadata
            results = collection.get(
                where={"$or": [{"body_terms": {"$contains": kw}} for kw in keywords]},
                limit=200
            )
            if results['documents']:
                chunks = [
                    (text, meta)
                    for text, meta in zip(results['documents'], results['metadatas'])
                ]
                print(f"Retrieved {len(chunks)} chunks for comparison")
    except Exception as e:
        print(f"Could not retrieve chunks: {e}")
        chunks = None
    
    reviewer = AnswerReviewer()
    results = reviewer.review(answer, chunks=chunks)
    
    # Print report
    reviewer.print_report(results, answer)
    
    return results, answer

if __name__ == "__main__":
    # Check if user wants to review saved answer
    if len(sys.argv) > 1 and sys.argv[1] in ["--saved", "-s"]:
        review_api_answer(use_saved=True)
    else:
        question = sys.argv[1] if len(sys.argv) > 1 else "Tell me about Vienna Rothschild banking"
        review_api_answer(question)

