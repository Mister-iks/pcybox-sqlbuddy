"""
Database connector module for MySQL and PostgreSQL
"""

from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors"""
    pass


class DatabaseConnector:
    """
    Handles database connections for MySQL and PostgreSQL
    """
    
    SUPPORTED_DATABASES = ["mysql", "postgresql"]
    
    def __init__(
        self,
        db_type: str = "mysql",
        host: str = "localhost",
        port: Optional[int] = None,
        user: str = "",
        password: str = "",
        database: str = "",
        **kwargs
    ):
        """
        Initialize database connector
        
        Args:
            db_type: Type of database ("mysql" or "postgresql")
            host: Database host
            port: Database port (default: 3306 for MySQL, 5432 for PostgreSQL)
            user: Database user
            password: Database password
            database: Database name
            **kwargs: Additional connection parameters
        """
        if db_type.lower() not in self.SUPPORTED_DATABASES:
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {', '.join(self.SUPPORTED_DATABASES)}"
            )
        
        self.db_type = db_type.lower()
        self.host = host
        self.port = port or self._get_default_port()
        self.user = user
        self.password = password
        self.database = database
        self.extra_params = kwargs
        self._connection = None
        
    def _get_default_port(self) -> int:
        """Get default port based on database type"""
        return 3306 if self.db_type == "mysql" else 5432
    
    def connect(self) -> None:
        """
        Establish connection to the database
        
        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            if self.db_type == "mysql":
                self._connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    **self.extra_params
                )
            else:  # postgresql
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.database,
                    cursor_factory=RealDictCursor,
                    **self.extra_params
                )
        except (pymysql.Error, psycopg2.Error) as e:
            raise DatabaseConnectionError(
                f"Failed to connect to {self.db_type} database: {str(e)}"
            )
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        if not self._connection:
            return False
        
        try:
            if self.db_type == "mysql":
                self._connection.ping(reconnect=False)
            else:  # postgresql
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return True
        except (pymysql.Error, psycopg2.Error):
            return False
    
    def ensure_connection(self) -> None:
        """Ensure connection is active, reconnect if necessary"""
        if not self.is_connected():
            self.connect()
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for getting a database cursor
        
        Yields:
            Database cursor
        """
        self.ensure_connection()
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query
        
        Args:
            query: SQL query to execute
            params: Query parameters (for parameterized queries)
            fetch: Whether to fetch results
            
        Returns:
            Query results as list of dictionaries if fetch=True, None otherwise
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            return None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information (without sensitive data)
        
        Returns:
            Dictionary with connection details
        """
        return {
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "database": self.database,
            "is_connected": self.is_connected()
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection
        
        Returns:
            Dictionary with test results
        """
        result = {
            "success": False,
            "message": "",
            "db_type": self.db_type,
            "database": self.database
        }
        
        try:
            self.connect()
            
            # Test query
            if self.db_type == "mysql":
                test_query = "SELECT VERSION() as version, DATABASE() as db_name"
            else:  # postgresql
                test_query = "SELECT version() as version, current_database() as db_name"
            
            test_result = self.execute_query(test_query)
            
            result["success"] = True
            result["message"] = "Connection successful"
            result["server_info"] = test_result[0] if test_result else {}
            
        except DatabaseConnectionError as e:
            result["message"] = str(e)
        except Exception as e:
            result["message"] = f"Unexpected error: {str(e)}"
        finally:
            self.disconnect()
        
        return result
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def __repr__(self) -> str:
        return (
            f"DatabaseConnector(db_type='{self.db_type}', "
            f"host='{self.host}', port={self.port}, "
            f"database='{self.database}')"
        )