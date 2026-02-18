"""
analyze_by_subproblems.py
Parse JSON output from subproblem agent and extract SQL clause types
"""

import json
import re
from typing import List


def parse_subproblems(sub_json: str) -> List[str]:
    """
    Extract SQL clause types from JSON output of subproblem agent
    
    Args:
        sub_json: JSON string containing subproblem decomposition
        
    Returns:
        List of SQL clause types, e.g., ['SELECT', 'WHERE', 'JOIN']
    """
    clauses = []
    
    try:
        # Try to parse JSON
        data = json.loads(sub_json)
        
        # Method 1: If JSON has "clauses" field
        if isinstance(data, dict) and "clauses" in data:
            clauses = data["clauses"]
        
        # Method 2: If JSON has "subproblems" field
        elif isinstance(data, dict) and "subproblems" in data:
            subproblems = data["subproblems"]
            if isinstance(subproblems, list):
                for subprob in subproblems:
                    if isinstance(subprob, dict) and "clause" in subprob:
                        clauses.append(subprob["clause"])
                    elif isinstance(subprob, str):
                        # Extract SQL keywords from text
                        extracted = extract_clauses_from_text(subprob)
                        clauses.extend(extracted)
        
        # Method 3: If it's list format
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "clause" in item:
                    clauses.append(item["clause"])
                elif isinstance(item, str):
                    extracted = extract_clauses_from_text(item)
                    clauses.extend(extracted)
        
        # Method 4: If entire JSON is text description, extract keywords from it
        else:
            text = json.dumps(data)
            clauses = extract_clauses_from_text(text)
    
    except json.JSONDecodeError:
        # If JSON parsing fails, extract directly from text
        clauses = extract_clauses_from_text(sub_json)
    
    # Deduplicate and return
    return list(set(clauses)) if clauses else []


def extract_clauses_from_text(text: str) -> List[str]:
    """
    Extract SQL clause keywords from text
    
    Args:
        text: Text containing SQL-related descriptions
        
    Returns:
        List of extracted SQL clauses
    """
    clauses = []
    text_upper = text.upper()
    
    # Define common SQL clause keywords and their variants
    clause_patterns = {
        'SELECT': ['SELECT', 'SELECTING', 'COLUMNS', 'FIELDS'],
        'FROM': ['FROM', 'TABLE', 'TABLES'],
        'WHERE': ['WHERE', 'FILTER', 'CONDITION', 'FILTERING'],
        'JOIN': ['JOIN', 'JOINING', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'OUTER JOIN'],
        'GROUP BY': ['GROUP BY', 'GROUPING', 'AGGREGATE', 'AGGREGATION'],
        'HAVING': ['HAVING'],
        'ORDER BY': ['ORDER BY', 'SORT', 'SORTING', 'ORDERING'],
        'LIMIT': ['LIMIT', 'TOP', 'FIRST'],
        'UNION': ['UNION'],
        'INTERSECT': ['INTERSECT'],
        'EXCEPT': ['EXCEPT', 'MINUS'],
        'DISTINCT': ['DISTINCT', 'UNIQUE'],
        'SUBQUERY': ['SUBQUERY', 'NESTED', 'INNER QUERY']
    }
    
    # Check each clause
    for clause, patterns in clause_patterns.items():
        for pattern in patterns:
            if pattern in text_upper:
                clauses.append(clause)
                break  # Break once found
    
    return clauses


# Test code
if __name__ == "__main__":
    # Test different JSON formats
    
    test_cases = [
        # Format 1: With clauses field
        '{"clauses": ["SELECT", "WHERE", "JOIN"]}',
        
        # Format 2: With subproblems field
        '{"subproblems": [{"clause": "SELECT"}, {"clause": "WHERE"}]}',
        
        # Format 3: Text description
        '{"steps": ["First, SELECT columns", "Then, use WHERE to filter"]}',
        
        # Format 4: Pure text
        "We need to SELECT, WHERE, and JOIN tables"
    ]
    
    print("Testing parse_subproblems function:")
    print("="*80)
    
    for i, test in enumerate(test_cases, 1):
        result = parse_subproblems(test)
        print(f"\nTest {i}:")
        print(f"Input: {test[:60]}...")
        print(f"Output: {result}")
    
    print("\n" + "="*80)
    print("Testing completed!")