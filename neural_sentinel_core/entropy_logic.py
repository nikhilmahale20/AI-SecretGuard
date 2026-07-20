#entropy_logic.py

import math
import re

# --- CONFIGURATION ---
ENTROPY_THRESHOLD = 4.5
MIN_STRING_LENGTH = 12

def calculate_shannon_entropy(data: str) -> float:
    """
    Calculates the Shannon Entropy of a string to detect randomness.
    Mathematical Formula: H(X) = -sum( P(x_i) * log2(P(x_i)) )
    """
    if not data:
        return 0.0
        
    entropy = 0.0
    data_length = len(data)
    
    # Calculate the probability of each unique character
    for char in set(data):
        p_x = data.count(char) / data_length
        entropy -= p_x * math.log2(p_x)
        
    return entropy

def extract_strings_from_line(line: str) -> list:
    """
    Extracts anything inside single or double quotes from a line of code.
    """
    # Regex to find text inside '...' or "..."
    return re.findall(r'["\'](.*?)["\']', line)

def is_high_entropy(string_literal: str) -> bool:
    """
    Evaluates if a string is long enough and random enough to be a secret.
    """
    if len(string_literal) > MIN_STRING_LENGTH:
        score = calculate_shannon_entropy(string_literal)
        if score > ENTROPY_THRESHOLD:
            return True, score
    return False, 0.0