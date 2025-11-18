"""
Fuzzy string matching utility for field labels and memory queries.
Uses Levenshtein distance ratio for similarity scoring.
"""

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    This is the minimum number of single-character edits required to change one string into the other.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity ratio between two strings (0.0 to 1.0).
    1.0 means exact match, 0.0 means completely different.
    """
    s1_normalized = s1.lower().strip()
    s2_normalized = s2.lower().strip()
    
    if s1_normalized == s2_normalized:
        return 1.0
    
    max_len = max(len(s1_normalized), len(s2_normalized))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(s1_normalized, s2_normalized)
    return 1.0 - (distance / max_len)


def fuzzy_match_field_label(field_label: str, memory_list: list, threshold: float = 0.8) -> dict:
    """
    Find the best matching memory entry for a given field label.
    
    Args:
        field_label: The label of the form field
        memory_list: List of memory entries (dicts with 'question_text' and 'answer_text')
        threshold: Minimum similarity ratio to consider a match (default 0.8 = 80%)
    
    Returns:
        Best matching memory entry, or None if no match above threshold
    """
    best_match = None
    best_similarity = 0.0
    
    for memory in memory_list:
        question = memory.get('question_text', '')
        similarity = similarity_ratio(field_label, question)
        
        if similarity > best_similarity and similarity >= threshold:
            best_similarity = similarity
            best_match = memory
    
    if best_match:
        print(f"[Fuzzy Match] '{field_label}' matched '{best_match['question_text']}' (similarity: {best_similarity:.2%})")
    
    return best_match


