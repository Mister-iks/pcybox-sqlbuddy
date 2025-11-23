"""
Tests for QueryGenerator
"""

import pytest
from unittest.mock import Mock, patch
from sqlbuddy.llm.query_generator import QueryGenerator, QueryGeneratorError, LLMProvider


def test_query_generator_initialization():
    """Test query generator initialization"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
        generator = QueryGenerator(provider="openai")
        
        assert generator.provider == LLMProvider.OPENAI
        assert generator.api_key == 'test_key'
        assert generator.temperature == 0.1


def test_unsupported_provider():
    """Test initialization with unsupported provider"""
    with pytest.raises(ValueError):
        QueryGenerator(provider="unsupported")


def test_missing_api_key():
    """Test initialization without API key"""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(QueryGeneratorError):
            QueryGenerator(provider="openai")


def test_build_prompt():
    """Test prompt building"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
        generator = QueryGenerator(provider="openai")
        
        prompt = generator._build_prompt(
            description="Get all users",
            schema="Table: users\nColumns: id, name, email",
            db_type="mysql"
        )
        
        assert "MySQL" in prompt.upper()
        assert "Get all users" in prompt
        assert "users" in prompt


def test_parse_response():
    """Test response parsing"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
        generator = QueryGenerator(provider="openai")
        
        response = """
        SQL QUERY:
```sql
        SELECT * FROM users WHERE id = 1;
```
        
        EXPLANATION:
        This query retrieves all columns for user with id 1.
        
        TABLES USED:
        - users
        """
        
        parsed = generator._parse_response(response, "mysql")
        
        assert "SELECT * FROM users" in parsed["query"]
        assert "users" in parsed["tables_used"]
        assert parsed["explanation"]


def test_get_provider_info():
    """Test getting provider info"""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
        generator = QueryGenerator(provider="openai", model="gpt-4")
        
        info = generator.get_provider_info()
        
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4"
        assert info["temperature"] == 0.1