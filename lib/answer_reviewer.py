"""
Answer Reviewer - Evaluates LLM answers against user criteria.

Flexible system for checking:
1. Paragraph length (max 3 sentences)
2. Chronological flow (forward progression, no backwards jumps)
3. Full history coverage (all eras present in chunks are covered)
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ReviewResult:
    """Result of reviewing an answer against criteria."""
    criterion: str
    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    issues: List[str]


class AnswerReviewer:
    """Review LLM answers against user-defined criteria."""
    
    def __init__(self):
        self.criteria = {
            'paragraph_length': self._check_paragraph_length,
            'chronological_flow': self._check_chronological_flow,
            'full_history': self._check_full_history,
            'panics_coverage': self._check_panics_coverage,
        }
    
    def review(self, answer: str, chunks: Optional[List[Tuple[str, dict]]] = None) -> Dict[str, ReviewResult]:
        """
        Review an answer against all criteria.
        
        Args:
            answer: The LLM-generated answer text
            chunks: Optional list of (text, metadata) tuples to check against
        
        Returns:
            Dict mapping criterion name to ReviewResult
        """
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
                    details=f"Error checking {criterion_name}: {e}",
                    issues=[f"Review error: {e}"]
                )
        
        return results
    
    def _check_paragraph_length(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        """Check that paragraphs don't exceed 3 sentences."""
        issues = []
        
        # Split into paragraphs (double newline)
        paras = [p.strip() for p in re.split(r'\n\s*\n+', answer) if p.strip()]
        
        # Skip section headers
        long_paras = []
        for i, para in enumerate(paras):
            # Skip headers (lines starting with **)
            if para.startswith('**') and '\n' not in para:
                continue
            
            # Count sentences
            sentences = self._count_sentences(para)
            if sentences > 3:
                long_paras.append((i+1, sentences, para[:100] + "..."))
                issues.append(f"Paragraph {i+1} has {sentences} sentences (max 3)")
        
        total_paras = len([p for p in paras if not (p.startswith('**') and '\n' not in p)])
        long_count = len(long_paras)
        
        if long_count == 0:
            return ReviewResult(
                criterion='paragraph_length',
                passed=True,
                score=1.0,
                details=f"All {total_paras} paragraphs are ≤3 sentences",
                issues=[]
            )
        else:
            score = max(0.0, 1.0 - (long_count / max(total_paras, 1)) * 0.5)
            return ReviewResult(
                criterion='paragraph_length',
                passed=False,
                score=score,
                details=f"{long_count}/{total_paras} paragraphs exceed 3 sentences",
                issues=issues[:5]  # Limit to first 5 issues
            )
    
    def _check_chronological_flow(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        """Check that answer progresses forward chronologically without backwards jumps."""
        issues = []
        
        # Extract all years mentioned in order
        years = []
        for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
            year = int(match.group(1))
            pos = match.start()
            years.append((year, pos))
        
        if len(years) < 2:
            return ReviewResult(
                criterion='chronological_flow',
                passed=True,
                score=1.0,
                details="Insufficient years to check chronological flow",
                issues=[]
            )
        
        # Check for backwards jumps (year mentioned after a later year)
        # But ignore if it's the same year mentioned multiple times (not a real jump)
        backwards_jumps = []
        seen_years = {}  # Track first occurrence of each year
        for i, (year, pos) in enumerate(years):
            if year not in seen_years:
                seen_years[year] = i
        
        for i in range(len(years) - 1):
            current_year, current_pos = years[i]
            # Check subsequent years, but only count significant backwards jumps (>10 years)
            for j in range(i + 1, len(years)):
                later_year, later_pos = years[j]
                if current_year > later_year and (current_year - later_year) > 10:
                    # Significant backwards jump - only count once per pair
                    pair = (later_year, current_year)
                    if pair not in backwards_jumps:
                        backwards_jumps.append(pair)
                        issues.append(f"Year {current_year} mentioned after {later_year} (backwards jump of {current_year - later_year} years)")
        
        # Also check if answer is organized chronologically overall
        # Split into paragraphs and check if years progress forward across paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n+', answer) if p.strip()]
        para_years = []
        for para in paragraphs:
            # Skip headers
            if para.startswith('**') and '\n' not in para:
                continue
            para_year_matches = list(re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', para))
            if para_year_matches:
                # Get earliest year in paragraph
                para_years.append(min(int(m.group(1)) for m in para_year_matches))
        
        # Check if paragraphs progress chronologically
        non_chronological = []
        if len(para_years) >= 2:
            for i in range(len(para_years) - 1):
                if para_years[i] > para_years[i+1] and (para_years[i] - para_years[i+1]) > 20:
                    non_chronological.append(f"Paragraph {i+1} ({para_years[i]}) comes before paragraph {i+2} ({para_years[i+1]}) - non-chronological organization")
            if non_chronological:
                issues.extend(non_chronological[:3])
        
        if not issues:
            return ReviewResult(
                criterion='chronological_flow',
                passed=True,
                score=1.0,
                details=f"Chronological flow maintained across {len(years)} year mentions",
                issues=[]
            )
        else:
            score = max(0.0, 1.0 - (len(backwards_jumps) / max(len(years), 1)) * 0.3 - len(non_chronological) * 0.2)
            details = f"{len(backwards_jumps)} backwards chronological jumps detected"
            if non_chronological:
                details += f", {len(non_chronological)} non-chronological paragraphs"
            return ReviewResult(
                criterion='chronological_flow',
                passed=False,
                score=score,
                details=details,
                issues=issues[:5]
            )
    
    def _check_full_history(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        """Check that answer covers all eras present in chunks."""
        if not chunks:
            return ReviewResult(
                criterion='full_history',
                passed=True,
                score=1.0,
                details="No chunks provided for comparison",
                issues=[]
            )
        
        # Extract years from chunks
        chunk_years = set()
        for text, _ in chunks:
            matches = re.findall(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', text)
            chunk_years.update(int(m) for m in matches)
        
        if not chunk_years:
            return ReviewResult(
                criterion='full_history',
                passed=True,
                score=1.0,
                details="No years found in chunks",
                issues=[]
            )
        
        chunk_latest = max(chunk_years)
        chunk_earliest = min(chunk_years)
        
        # Extract years from answer
        answer_years = set()
        for match in re.finditer(r'\b(1[6-9]\d{2}|20[0-2]\d)\b', answer):
            answer_years.add(int(match.group(1)))
        
        if not answer_years:
            return ReviewResult(
                criterion='full_history',
                passed=False,
                score=0.0,
                details=f"Answer has no years, but chunks span {chunk_earliest}-{chunk_latest}",
                issues=[f"Missing all historical coverage: chunks go to {chunk_latest}"]
            )
        
        answer_latest = max(answer_years)
        answer_earliest = min(answer_years)
        
        # Check if answer stops early
        gap = chunk_latest - answer_latest
        issues = []
        
        if gap > 20:  # More than 20 years gap
            issues.append(f"Answer stops at {answer_latest}, but chunks go to {chunk_latest} (gap: {gap} years)")
        
        # Check if answer misses early periods
        if answer_earliest > chunk_earliest + 50:  # More than 50 years later
            issues.append(f"Answer starts at {answer_earliest}, but chunks start at {chunk_earliest} (missing early period)")
        
        # Check coverage of major eras
        eras_missing = []
        if chunk_latest >= 1900 and answer_latest < 1900:
            eras_missing.append("20th century")
        if chunk_latest >= 2000 and answer_latest < 2000:
            eras_missing.append("21st century")
        if chunk_latest >= 1800 and answer_earliest > 1800:
            # Check if 18th century is covered
            if not any(y < 1800 for y in answer_years):
                eras_missing.append("18th century")
        
        if eras_missing:
            issues.append(f"Missing eras: {', '.join(eras_missing)}")
        
        if not issues:
            return ReviewResult(
                criterion='full_history',
                passed=True,
                score=1.0,
                details=f"Full coverage: answer spans {answer_earliest}-{answer_latest}, chunks span {chunk_earliest}-{chunk_latest}",
                issues=[]
            )
        else:
            # Calculate score based on gap
            if gap > 0:
                score = max(0.0, 1.0 - (gap / 100.0))  # Penalize large gaps
            else:
                score = 0.8  # Some other issue
            
            return ReviewResult(
                criterion='full_history',
                passed=False,
                score=score,
                details=f"Incomplete coverage: answer {answer_earliest}-{answer_latest}, chunks {chunk_earliest}-{chunk_latest} (gap: {gap} years)",
                issues=issues
            )
    
    def _check_panics_coverage(self, answer: str, chunks: Optional[List] = None) -> ReviewResult:
        """Check if answer mentions panics/crises that are present in chunks."""
        if not chunks:
            return ReviewResult(
                criterion='panics_coverage',
                passed=True,
                score=1.0,
                details="No chunks provided for panic check",
                issues=[]
            )
        
        # Find panics in chunks
        panic_keywords = ['panic of', 'panic', 'crisis', 'crash', 'depression', 'recession', 'bubble', 'run']
        panic_years = ['1763', '1772', '1792', '1819', '1825', '1837', '1847', '1857', '1866', '1873', 
                      '1884', '1890', '1893', '1896', '1901', '1907', '1910', '1914', '1920', '1929',
                      '1931', '1973', '1987', '1997', '1998', '2001', '2007', '2008', '2009']
        
        chunks_text = ' '.join([text for text, _ in chunks])
        panics_in_chunks = set()
        
        # Check for panic mentions in chunks
        for keyword in panic_keywords:
            if keyword in chunks_text.lower():
                # Try to extract year nearby
                pattern = rf'{re.escape(keyword)}[^.]*?\b(1[6-9]\d{{2}}|20[0-2]\d)\b'
                matches = re.finditer(pattern, chunks_text.lower())
                for match in matches:
                    year = match.group(1)
                    panics_in_chunks.add(f"{keyword} {year}")
        
        # Also check for specific panic years
        for year in panic_years:
            if year in chunks_text:
                panics_in_chunks.add(f"panic/crisis {year}")
        
        if not panics_in_chunks:
            return ReviewResult(
                criterion='panics_coverage',
                passed=True,
                score=1.0,
                details="No panics/crises found in chunks",
                issues=[]
            )
        
        # Check if answer mentions panics
        answer_lower = answer.lower()
        panics_mentioned = []
        panics_missing = []
        
        for panic in panics_in_chunks:
            # Check if panic is mentioned in answer
            panic_words = panic.split()
            if any(word in answer_lower for word in panic_words):
                panics_mentioned.append(panic)
            else:
                panics_missing.append(panic)
        
        if not panics_missing:
            return ReviewResult(
                criterion='panics_coverage',
                passed=True,
                score=1.0,
                details=f"All {len(panics_mentioned)} panics/crises from chunks are mentioned",
                issues=[]
            )
        
        score = len(panics_mentioned) / len(panics_in_chunks) if panics_in_chunks else 0.0
        return ReviewResult(
            criterion='panics_coverage',
            passed=False,
            score=score,
            details=f"Missing {len(panics_missing)}/{len(panics_in_chunks)} panics/crises: {', '.join(panics_missing[:3])}",
            issues=[f"Missing panic/crisis: {p}" for p in panics_missing[:5]]
        )
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Split on sentence-ending punctuation followed by space and capital letter
        sentences = re.split(r'[.!?]+\s+(?=[A-Z])', text)
        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        # If no splits found, try simpler approach
        if len(sentences) == 1:
            # Count punctuation marks
            sentences = re.findall(r'[^.!?]*[.!?]+', text)
        return len(sentences) if sentences else 1
    
    def print_report(self, results: Dict[str, ReviewResult], answer: str = None):
        """Print a formatted review report with actionable failures."""
        print("\n" + "="*70)
        print("ANSWER REVIEW REPORT")
        print("="*70)
        
        all_passed = all(r.passed for r in results.values())
        failures = []
        
        for criterion, result in results.items():
            if result.passed:
                print(f"\n[PASS] - {result.criterion.upper().replace('_', ' ')}")
                # Replace Unicode characters that cause encoding issues
                details_safe = result.details.replace('≤', '<=').replace('≥', '>=')
                print(f"  {details_safe}")
            else:
                print(f"\n[FAIL] - {result.criterion.upper().replace('_', ' ')}")
                details_safe = result.details.replace('≤', '<=').replace('≥', '>=')
                print(f"  {details_safe}")
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

