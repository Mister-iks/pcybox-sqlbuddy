"""
Tests for DatabaseConnector
"""

import pytest
from sqlbuddy.core.connector import DatabaseConnector, DatabaseConnectionError


def test_connector_initialization():
    """Test connector initialization with default values"""
    connector = DatabaseConnector(
        db_type="mysql",
        host="localhost",
        user="test_user",
        password="test_pass",
        database="test_db"
    )
    
    assert connector.db_type == "mysql"
    assert connector.host == "localhost"
    assert connector.port == 3306
    assert connector.database == "test_db"


def test_postgresql_default_port():
    """Test PostgreSQL default port"""
    connector = DatabaseConnector(
        db_type="postgresql",
        host="localhost",
        user="test_user",
        password="test_pass",
        database="test_db"
    )
    
    assert connector.port == 5432


def test_unsupported_database_type():
    """Test initialization with unsupported database type"""
    with pytest.raises(ValueError):
        DatabaseConnector(
            db_type="mongodb",
            host="localhost",
            user="test",
            password="test",
            database="test"
        )


def test_get_connection_info():
    """Test getting connection info"""
    connector = DatabaseConnector(
        db_type="mysql",
        host="localhost",
        user="test_user",
        password="secret",
        database="test_db"
    )
    
    info = connector.get_connection_info()
    
    assert info["db_type"] == "mysql"
    assert info["host"] == "localhost"
    assert info["database"] == "test_db"
    assert info["user"] == "test_user"
    assert "password" not in info  # Password should not be in info


def test_connector_repr():
    """Test string representation"""
    connector = DatabaseConnector(
        db_type="mysql",
        host="localhost",
        user="test",
        password="test",
        database="test_db"
    )
    
    repr_str = repr(connector)
    assert "mysql" in repr_str
    assert "test_db" in repr_str