"""
Query generator module using LLM (OpenAI GPT and Anthropic Claude)
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import os
import re
from openai import OpenAI
from anthropic import Anthropic


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    CLAUDE = "claude"


class QueryGeneratorError(Exception):
    """Exception raised for query generation errors"""
    pass


class QueryGenerator:
    """
    Generates SQL queries using LLM based on natural language descriptions
    """
    
    DEFAULT_MODELS = {
        LLMProvider.OPENAI: "gpt-4-turbo-preview",
        LLMProvider.CLAUDE: "claude-3-5-sonnet-20241022"
    }
    
    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ):
        """
        Initialize query generator
        
        Args:
            provider: LLM provider ("openai" or "claude")
            api_key: API key for the provider (if None, will use env variables)
            model: Model name (if None, will use default for provider)
            temperature: Temperature for generation (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        try:
            self.provider = LLMProvider(provider.lower())
        except ValueError:
            raise ValueError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join([p.value for p in LLMProvider])}"
            )
        
        self.model = model or self.DEFAULT_MODELS[self.provider]
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize LLM client
        if self.provider == LLMProvider.OPENAI:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise QueryGeneratorError(
                    "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self.client = OpenAI(api_key=self.api_key)
        
        elif self.provider == LLMProvider.CLAUDE:
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise QueryGeneratorError(
                    "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                    "or pass api_key parameter."
                )
            self.client = Anthropic(api_key=self.api_key)
    
    def generate_query(
        self,
        description: str,
        schema: str,
        db_type: str = "mysql",
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language description
        
        Args:
            description: Natural language description of the desired query
            schema: Database schema formatted as string
            db_type: Database type ("mysql" or "postgresql")
            additional_context: Additional context or constraints
            
        Returns:
            Dictionary containing generated query and metadata
        """
        prompt = self._build_prompt(description, schema, db_type, additional_context)
        
        try:
            if self.provider == LLMProvider.OPENAI:
                response = self._generate_with_openai(prompt)
            else:  # Claude
                response = self._generate_with_claude(prompt)
            
            # Parse and validate the response
            parsed = self._parse_response(response, db_type)
            
            return parsed
        
        except Exception as e:
            raise QueryGeneratorError(f"Failed to generate query: {str(e)}")
    
    def _build_prompt(
        self,
        description: str,
        schema: str,
        db_type: str,
        additional_context: Optional[str] = None
    ) -> str:
        """
        Build the prompt for the LLM
        
        Args:
            description: User's natural language description
            schema: Database schema
            db_type: Database type
            additional_context: Additional context
            
        Returns:
            Complete prompt string
        """
        prompt_parts = [
            f"You are an expert SQL query generator for {db_type.upper()} databases.",
            "",
            "Your task is to generate a SQL query based on the user's natural language description.",
            "",
            "IMPORTANT RULES:",
            "1. Generate ONLY valid SQL queries for the specified database type",
            "2. Use ONLY tables and columns that exist in the provided schema",
            "3. Follow SQL best practices and optimization techniques",
            "4. Include appropriate JOINs when querying multiple tables",
            "5. Use proper WHERE clauses for filtering",
            "6. Add ORDER BY, LIMIT, or GROUP BY when relevant",
            "7. Ensure the query is safe and doesn't include any destructive operations unless explicitly requested",
            "8. If the request is ambiguous, make reasonable assumptions based on the schema",
            "",
            "DATABASE SCHEMA:",
            "=" * 80,
            schema,
            "=" * 80,
            "",
        ]
        
        if additional_context:
            prompt_parts.extend([
                "ADDITIONAL CONTEXT:",
                additional_context,
                "",
            ])
        
        prompt_parts.extend([
            "USER REQUEST:",
            description,
            "",
            "Please provide your response in the following format:",
            "",
            "SQL QUERY:",
            "```sql",
            "[Your SQL query here]",
            "```",
            "",
            "EXPLANATION:",
            "[Brief explanation of what the query does and any assumptions made]",
            "",
            "TABLES USED:",
            "[List of tables used in the query]",
            "",
            "POTENTIAL OPTIMIZATIONS:",
            "[Optional suggestions for query optimization if applicable]"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_with_openai(self, prompt: str) -> str:
        """
        Generate response using OpenAI
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Generated response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SQL query generator. Generate accurate, "
                               "efficient, and safe SQL queries based on user descriptions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def _generate_with_claude(self, prompt: str) -> str:
        """
        Generate response using Anthropic Claude
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Generated response text
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        return response.content[0].text
    
    def _parse_response(self, response: str, db_type: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract query and metadata
        
        Args:
            response: Raw LLM response
            db_type: Database type
            
        Returns:
            Parsed response dictionary
        """
        result = {
            "query": "",
            "explanation": "",
            "tables_used": [],
            "optimizations": "",
            "raw_response": response
        }
        
        # Extract SQL query from code blocks
        sql_pattern = r"```sql\s*(.*?)\s*```"
        sql_matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if sql_matches:
            result["query"] = sql_matches[0].strip()
        else:
            # Try to find any SQL-like content
            lines = response.split('\n')
            sql_lines = []
            in_sql = False
            
            for line in lines:
                line_lower = line.lower().strip()
                if any(keyword in line_lower for keyword in ['select', 'insert', 'update', 'delete', 'create']):
                    in_sql = True
                
                if in_sql:
                    sql_lines.append(line)
                    if line.strip().endswith(';'):
                        break
            
            if sql_lines:
                result["query"] = '\n'.join(sql_lines).strip()
        
        # Extract explanation
        explanation_pattern = r"EXPLANATION:\s*(.*?)(?=TABLES USED:|POTENTIAL OPTIMIZATIONS:|$)"
        explanation_match = re.search(explanation_pattern, response, re.DOTALL | re.IGNORECASE)
        if explanation_match:
            result["explanation"] = explanation_match.group(1).strip()
        
        # Extract tables used
        tables_pattern = r"TABLES USED:\s*(.*?)(?=POTENTIAL OPTIMIZATIONS:|$)"
        tables_match = re.search(tables_pattern, response, re.DOTALL | re.IGNORECASE)
        if tables_match:
            tables_text = tables_match.group(1).strip()
            # Extract table names from list format
            result["tables_used"] = [
                line.strip('- \n') 
                for line in tables_text.split('\n') 
                if line.strip() and line.strip() != '-'
            ]
        
        # Extract optimizations
        opt_pattern = r"POTENTIAL OPTIMIZATIONS:\s*(.*?)$"
        opt_match = re.search(opt_pattern, response, re.DOTALL | re.IGNORECASE)
        if opt_match:
            result["optimizations"] = opt_match.group(1).strip()
        
        # Validate that we got a query
        if not result["query"]:
            raise QueryGeneratorError(
                "Failed to extract SQL query from LLM response. "
                "The response may be in an unexpected format."
            )
        
        return result
    
    def generate_multiple_queries(
        self,
        description: str,
        schema: str,
        db_type: str = "mysql",
        num_variations: int = 3,
        additional_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple query variations for the same description
        
        Args:
            description: Natural language description
            schema: Database schema
            db_type: Database type
            num_variations: Number of variations to generate
            additional_context: Additional context
            
        Returns:
            List of query variations with metadata
        """
        variations = []
        
        for i in range(num_variations):
            context = additional_context or ""
            context += f"\n\nGenerate variation #{i+1} with different approach/optimization."
            
            try:
                query_result = self.generate_query(
                    description,
                    schema,
                    db_type,
                    context
                )
                query_result["variation_number"] = i + 1
                variations.append(query_result)
            except QueryGeneratorError as e:
                # Continue with other variations if one fails
                variations.append({
                    "variation_number": i + 1,
                    "error": str(e)
                })
        
        return variations
    
    def explain_query(
        self,
        query: str,
        schema: str,
        db_type: str = "mysql"
    ) -> Dict[str, Any]:
        """
        Get explanation for an existing SQL query
        
        Args:
            query: SQL query to explain
            schema: Database schema
            db_type: Database type
            
        Returns:
            Dictionary with explanation and analysis
        """
        prompt_parts = [
            f"You are an expert SQL analyst for {db_type.upper()} databases.",
            "",
            "Analyze the following SQL query and provide:",
            "1. A clear explanation of what the query does",
            "2. Performance analysis",
            "3. Potential issues or improvements",
            "4. Tables and columns used",
            "",
            "DATABASE SCHEMA:",
            "=" * 80,
            schema,
            "=" * 80,
            "",
            "SQL QUERY TO ANALYZE:",
            "```sql",
            query,
            "```",
            "",
            "Please provide your analysis in a structured format."
        ]
        
        prompt = "\n".join(prompt_parts)
        
        try:
            if self.provider == LLMProvider.OPENAI:
                response = self._generate_with_openai(prompt)
            else:
                response = self._generate_with_claude(prompt)
            
            return {
                "query": query,
                "analysis": response,
                "db_type": db_type
            }
        
        except Exception as e:
            raise QueryGeneratorError(f"Failed to explain query: {str(e)}")
    
    def optimize_query(
        self,
        query: str,
        schema: str,
        db_type: str = "mysql"
    ) -> Dict[str, Any]:
        """
        Get optimization suggestions for a SQL query
        
        Args:
            query: SQL query to optimize
            schema: Database schema
            db_type: Database type
            
        Returns:
            Dictionary with original query, optimized version, and explanations
        """
        prompt_parts = [
            f"You are an expert SQL performance optimizer for {db_type.upper()} databases.",
            "",
            "Analyze the following SQL query and provide an optimized version.",
            "",
            "Consider:",
            "- Index usage",
            "- JOIN optimization",
            "- Subquery optimization",
            "- Proper use of WHERE clauses",
            "- Avoiding SELECT *",
            "- Using appropriate data types",
            "",
            "DATABASE SCHEMA:",
            "=" * 80,
            schema,
            "=" * 80,
            "",
            "ORIGINAL QUERY:",
            "```sql",
            query,
            "```",
            "",
            "Provide:",
            "1. OPTIMIZED QUERY (in SQL code block)",
            "2. Explanation of optimizations made",
            "3. Performance impact estimation",
        ]
        
        prompt = "\n".join(prompt_parts)
        
        try:
            if self.provider == LLMProvider.OPENAI:
                response = self._generate_with_openai(prompt)
            else:
                response = self._generate_with_claude(prompt)
            
            # Extract optimized query
            sql_pattern = r"```sql\s*(.*?)\s*```"
            sql_matches = re.findall(sql_pattern, response, re.DOTALL | re.IGNORECASE)
            
            optimized_query = sql_matches[0].strip() if sql_matches else ""
            
            return {
                "original_query": query,
                "optimized_query": optimized_query,
                "optimization_details": response,
                "db_type": db_type
            }
        
        except Exception as e:
            raise QueryGeneratorError(f"Failed to optimize query: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about current LLM provider configuration
        
        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }