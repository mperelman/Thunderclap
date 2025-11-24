"""
Shared text processing utilities.
Extracted from duplicate implementations across the codebase.
"""
import re


def split_into_sentences(text: str) -> list:
    """
    Split text into sentences, preserving punctuation.
    
    Args:
        text: Text to split
        
    Returns:
        List of sentences (strings)
    """
    # Split on sentence endings, but preserve them
    sentences = re.split(r'([.!?]+)\s+', text)
    result = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = (sentences[i] + sentences[i + 1]).strip()
            if sentence:
                result.append(sentence)
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    return result if result else [text]


def extract_phrases(text: str, min_words: int = 5) -> set:
    """
    Extract meaningful phrases from text.
    
    Args:
        text: Text to extract phrases from
        min_words: Minimum words per phrase
        
    Returns:
        Set of phrases (strings)
    """
    sentences = split_into_sentences(text)
    phrases = set()
    for sentence in sentences:
        words = sentence.split()
        if len(words) >= min_words:
            # Add full sentence as phrase
            phrases.add(sentence)
            # Add sub-phrases of 5+ words
            for i in range(len(words) - min_words + 1):
                phrase = ' '.join(words[i:i + min_words])
                if len(phrase.split()) >= min_words:
                    phrases.add(phrase)
    return phrases



