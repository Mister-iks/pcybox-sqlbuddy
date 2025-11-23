"""
Main SQLBuddy class - High-level API
"""

from typing import Dict, Any, Optional, List
from sqlbuddy.core.connector import DatabaseConnector, DatabaseConnectionError
from sqlbuddy.core.schema_extractor import SchemaExtractor
from sqlbuddy.llm.query_generator import QueryGenerator, QueryGeneratorError
from sqlbuddy.utils.validators import QueryValidator
from sqlbuddy.utils.logger import setup_logger
import logging


class SQLBuddy:
    """
    Main class for SQL Buddy - AI-powered SQL query generator
    
    This class provides a high-level interface to:
    - Connect to databases (MySQL, PostgreSQL)
    - Extract database schema
    - Generate SQL queries from natural language using AI
    - Validate and execute queries
    """
    
    def __init__(
        self,
        db_type: str = "mysql",
        host: str = "localhost",
        port: Optional[int] = None,
        user: str = "",
        password: str = "",
        database: str = "",
        llm_provider: str = "openai",
        api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
        temperature: float = 0.1,
        auto_connect: bool = True,
        log_level: int = logging.INFO,
        **kwargs
    ):
        """
        Initialize SQL Buddy
        
        Args:
            db_type: Database type ("mysql" or "postgresql")
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            llm_provider: LLM provider ("openai" or "claude")
            api_key: API key for LLM provider
            llm_model: Specific model to use
            temperature: Temperature for LLM generation
            auto_connect: Automatically connect to database on initialization
            log_level: Logging level
            **kwargs: Additional database connection parameters
        """
        # Setup logger
        self.logger = setup_logger("sqlbuddy", level=log_level)
        
        # Initialize database connector
        self.logger.info(f"Initializing SQL Buddy for {db_type} database: {database}")
        self.connector = DatabaseConnector(
            db_type=db_type,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            **kwargs
        )
        
        # Initialize schema extractor
        self.schema_extractor = SchemaExtractor(self.connector)
        
        # Initialize query generator
        self.logger.info(f"Initializing {llm_provider} query generator")
        self.query_generator = QueryGenerator(
            provider=llm_provider,
            api_key=api_key,
            model=llm_model,
            temperature=temperature
        )
        
        # Cache for schema
        self._cached_schema = None
        self._cached_schema_formatted = None
        
        # Connect to database if auto_connect is True
        if auto_connect:
            self.connect()
    
    def connect(self) -> Dict[str, Any]:
        """
        Connect to the database
        
        Returns:
            Connection test results
        """
        self.logger.info("Testing database connection...")
        result = self.connector.test_connection()
        
        if result["success"]:
            self.logger.info("Successfully connected to database")
            # Pre-load schema
            self.load_schema()
        else:
            self.logger.error(f"Failed to connect: {result['message']}")
        
        return result
    
    def disconnect(self):
        """Disconnect from the database"""
        self.connector.disconnect()
        self.logger.info("Disconnected from database")
    
    def load_schema(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load and cache database schema
        
        Args:
            force_reload: Force reload schema even if cached
            
        Returns:
            Database schema dictionary
        """
        if force_reload or not self._cached_schema:
            self.logger.info("Loading database schema...")
            self._cached_schema = self.schema_extractor.extract_full_schema(use_cache=False)
            self._cached_schema_formatted = self.schema_extractor.format_schema_for_llm()
            self.logger.info(f"Schema loaded: {len(self._cached_schema['tables'])} tables found")
        
        return self._cached_schema
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the database schema
        
        Returns:
            Schema summary dictionary
        """
        if not self._cached_schema:
            self.load_schema()
        
        return self.schema_extractor.get_schema_summary()
    
    def generate_query(
        self,
        description: str,
        validate: bool = True,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language description
        
        Args:
            description: Natural language description of desired query
            validate: Whether to validate the generated query
            additional_context: Additional context for query generation
            
        Returns:
            Dictionary containing generated query and metadata
        """
        if not self._cached_schema_formatted:
            self.load_schema()
        
        self.logger.info(f"Generating query for: {description}")
        
        try:
            # Generate query using LLM
            result = self.query_generator.generate_query(
                description=description,
                schema=self._cached_schema_formatted,
                db_type=self.connector.db_type,
                additional_context=additional_context
            )
            
            # Validate query if requested
            if validate:
                validation = QueryValidator.validate_query(result["query"])
                result["validation"] = validation
                
                if not validation["is_valid"]:
                    self.logger.warning(f"Generated query failed validation: {validation['errors']}")
                elif validation["warnings"]:
                    self.logger.warning(f"Query validation warnings: {validation['warnings']}")
            
            self.logger.info("Query generated successfully")
            return result
        
        except QueryGeneratorError as e:
            self.logger.error(f"Failed to generate query: {str(e)}")
            raise
    
    def generate_multiple_queries(
        self,
        description: str,
        num_variations: int = 3,
        validate: bool = True,
        additional_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple query variations
        
        Args:
            description: Natural language description
            num_variations: Number of variations to generate
            validate: Whether to validate queries
            additional_context: Additional context
            
        Returns:
            List of query variations with metadata
        """
        if not self._cached_schema_formatted:
            self.load_schema()
        
        self.logger.info(f"Generating {num_variations} query variations for: {description}")
        
        try:
            variations = self.query_generator.generate_multiple_queries(
                description=description,
                schema=self._cached_schema_formatted,
                db_type=self.connector.db_type,
                num_variations=num_variations,
                additional_context=additional_context
            )
            
            # Validate each variation if requested
            if validate:
                for variation in variations:
                    if "query" in variation:
                        validation = QueryValidator.validate_query(variation["query"])
                        variation["validation"] = validation
            
            self.logger.info(f"Generated {len(variations)} variations")
            return variations
        
        except QueryGeneratorError as e:
            self.logger.error(f"Failed to generate variations: {str(e)}")
            raise
    
    def execute_query(
        self,
        query: str,
        validate: bool = True,
        allow_destructive: bool = False,
        params: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query
        
        Args:
            query: SQL query to execute
            validate: Whether to validate before execution
            allow_destructive: Allow destructive operations
            params: Query parameters for parameterized queries
            
        Returns:
            Dictionary with query results and metadata
        """
        result = {
            "query": query,
            "success": False,
            "data": None,
            "row_count": 0,
            "error": None
        }
        
        # Validate query
        if validate:
            validation = QueryValidator.validate_query(query, allow_destructive=allow_destructive)
            result["validation"] = validation
            
            if not validation["is_valid"]:
                result["error"] = f"Query validation failed: {validation['errors']}"
                self.logger.error(result["error"])
                return result
            
            if validation["warnings"]:
                self.logger.warning(f"Query warnings: {validation['warnings']}")
        
        try:
            self.logger.info(f"Executing query: {query[:100]}...")
            
            # Execute query
            query_upper = query.upper().strip()
            is_select = query_upper.startswith('SELECT')
            
            data = self.connector.execute_query(query, params, fetch=is_select)
            
            result["success"] = True
            result["data"] = data
            result["row_count"] = len(data) if data else 0
            
            self.logger.info(f"Query executed successfully. Rows affected/returned: {result['row_count']}")
        
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Query execution failed: {str(e)}")
        
        return result
    
    def generate_and_execute(
        self,
        description: str,
        validate: bool = True,
        allow_destructive: bool = False,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate and immediately execute a query
        
        Args:
            description: Natural language description
            validate: Whether to validate
            allow_destructive: Allow destructive operations
            additional_context: Additional context
            
        Returns:
            Dictionary with generation and execution results
        """
        # Generate query
        generation_result = self.generate_query(
            description=description,
            validate=validate,
            additional_context=additional_context
        )
        
        if not generation_result.get("query"):
            return {
                "generation": generation_result,
                "execution": {"error": "No query generated"}
            }
        
        # Execute query
        execution_result = self.execute_query(
            query=generation_result["query"],
            validate=validate,
            allow_destructive=allow_destructive
        )
        
        return {
            "generation": generation_result,
            "execution": execution_result
        }
    
    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Get explanation for a SQL query
        
        Args:
            query: SQL query to explain
            
        Returns:
            Dictionary with query explanation
        """
        if not self._cached_schema_formatted:
            self.load_schema()
        
        self.logger.info("Generating query explanation...")
        
        try:
            result = self.query_generator.explain_query(
                query=query,
                schema=self._cached_schema_formatted,
                db_type=self.connector.db_type
            )
            
            self.logger.info("Explanation generated successfully")
            return result
        
        except QueryGeneratorError as e:
            self.logger.error(f"Failed to explain query: {str(e)}")
            raise
    
    def optimize_query(self, query: str) -> Dict[str, Any]:
        """
        Get optimization suggestions for a query
        
        Args:
            query: SQL query to optimize
            
        Returns:
            Dictionary with original and optimized query
        """
        if not self._cached_schema_formatted:
            self.load_schema()
        
        self.logger.info("Generating query optimizations...")
        
        try:
            result = self.query_generator.optimize_query(
                query=query,
                schema=self._cached_schema_formatted,
                db_type=self.connector.db_type
            )
            
            self.logger.info("Optimization generated successfully")
            return result
        
        except QueryGeneratorError as e:
            self.logger.error(f"Failed to optimize query: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information dictionary or None
        """
        if not self._cached_schema:
            self.load_schema()
        
        return self.schema_extractor.get_table_info(table_name)
    
    def list_tables(self) -> List[str]:
        """
        Get list of all tables in the database
        
        Returns:
            List of table names
        """
        summary = self.get_schema_summary()
        return summary.get("table_names", [])
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of SQL Buddy
        
        Returns:
            Status information dictionary
        """
        return {
            "database": self.connector.get_connection_info(),
            "llm": self.query_generator.get_provider_info(),
            "schema_loaded": self._cached_schema is not None,
            "schema_summary": self.get_schema_summary() if self._cached_schema else None
        }
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def __repr__(self) -> str:
        return (
            f"SQLBuddy(database='{self.connector.database}', "
            f"db_type='{self.connector.db_type}', "
            f"llm_provider='{self.query_generator.provider.value}')"
        )