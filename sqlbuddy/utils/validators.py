"""
Query validation utilities
"""

import re
from typing import List, Dict, Any


class QueryValidator:
    """
    Validates SQL queries for safety and correctness
    """
    
    # Dangerous SQL patterns that should be blocked or warned about
    DANGEROUS_PATTERNS = [
        r'\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)',  # DELETE without WHERE
        r'\bUPDATE\s+\w+\s+SET\s+.*(?:;|$)',  # UPDATE without WHERE (simplified)
        r'\bGRANT\b',
        r'\bREVOKE\b',
        r'\bALTER\s+TABLE\b',
        r'\bCREATE\s+(?:USER|ROLE)\b',
        r'\bDROP\s+(?:USER|ROLE)\b',
    ]
    
    # SQL injection patterns
    INJECTION_PATTERNS = [
        r"(?:;|--|\#|\/\*|\*\/)",  # Common SQL injection characters
        r"(?:'|\")(?:\s*(?:OR|AND)\s*(?:'|\d))",  # OR/AND injection
        r"UNION\s+(?:ALL\s+)?SELECT",  # UNION injection
        r"(?:EXEC|EXECUTE)\s*\(",  # Command execution
    ]
    
    @staticmethod
    def validate_query(query: str, allow_destructive: bool = False) -> Dict[str, Any]:
        """
        Validate a SQL query for safety and correctness
        
        Args:
            query: SQL query to validate
            allow_destructive: Whether to allow destructive operations
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "is_destructive": False,
            "is_suspicious": False,
        }
        
        if not query or not query.strip():
            result["is_valid"] = False
            result["errors"].append("Query is empty")
            return result
        
        query_upper = query.upper()
        
        # Check for dangerous patterns
        for pattern in QueryValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                result["is_destructive"] = True
                if not allow_destructive:
                    result["is_valid"] = False
                    result["errors"].append(
                        f"Destructive operation detected: {pattern}. "
                        "Set allow_destructive=True to bypass this check."
                    )
                else:
                    result["warnings"].append(
                        f"Destructive operation detected: {pattern}"
                    )
        
        # Check for SQL injection patterns
        for pattern in QueryValidator.INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                result["is_suspicious"] = True
                result["warnings"].append(
                    f"Potentially suspicious pattern detected: {pattern}"
                )
        
        # Check for basic SQL syntax issues
        if not any(keyword in query_upper for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
            result["is_valid"] = False
            result["errors"].append("No valid SQL command found")
        
        # Check for unbalanced parentheses
        if query.count('(') != query.count(')'):
            result["warnings"].append("Unbalanced parentheses detected")
        
        # Check for unbalanced quotes
        if query.count("'") % 2 != 0 or query.count('"') % 2 != 0:
            result["warnings"].append("Unbalanced quotes detected")
        
        return result
    
    @staticmethod
    def is_safe_query(query: str) -> bool:
        """
        Quick check if a query is safe to execute
        
        Args:
            query: SQL query to check
            
        Returns:
            True if query appears safe, False otherwise
        """
        validation = QueryValidator.validate_query(query, allow_destructive=False)
        return validation["is_valid"] and not validation["is_suspicious"]
    
    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Basic sanitization of SQL query
        
        Args:
            query: Query to sanitize
            
        Returns:
            Sanitized query
        """
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        # Remove trailing semicolon if present
        query = query.rstrip(';')
        
        return query.strip()
    
    @staticmethod
    def extract_tables_from_query(query: str) -> List[str]:
        """
        Extract table names from a SQL query
        
        Args:
            query: SQL query
            
        Returns:
            List of table names found in the query
        """
        tables = []
        
        # Pattern to match table names after FROM and JOIN
        patterns = [
            r'FROM\s+([`"]?\w+[`"]?)',
            r'JOIN\s+([`"]?\w+[`"]?)',
            r'INTO\s+([`"]?\w+[`"]?)',
            r'UPDATE\s+([`"]?\w+[`"]?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            tables.extend([match.strip('`"') for match in matches])
        
        return list(set(tables))  # Remove duplicates