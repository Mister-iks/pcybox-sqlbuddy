"""
Tests for SchemaExtractor
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlbuddy.core.connector import DatabaseConnector
from sqlbuddy.core.schema_extractor import SchemaExtractor


@pytest.fixture
def mock_connector():
    """Create a mock database connector"""
    connector = Mock(spec=DatabaseConnector)
    connector.db_type = "mysql"
    connector.database = "test_db"
    connector.execute_query = MagicMock()
    return connector


def test_schema_extractor_initialization(mock_connector):
    """Test schema extractor initialization"""
    extractor = SchemaExtractor(mock_connector)
    
    assert extractor.connector == mock_connector
    assert extractor.db_type == "mysql"
    assert extractor._schema_cache is None


def test_get_table_names_mysql(mock_connector):
    """Test getting table names for MySQL"""
    mock_connector.execute_query.return_value = [
        {'TABLE_NAME': 'users'},
        {'TABLE_NAME': 'posts'},
    ]
    
    extractor = SchemaExtractor(mock_connector)
    table_names = extractor._get_table_names()
    
    assert table_names == ['users', 'posts']
    assert mock_connector.execute_query.called


def test_get_schema_summary(mock_connector):
    """Test getting schema summary"""
    # Mock the full schema extraction
    mock_connector.execute_query.side_effect = [
        [{'TABLE_NAME': 'users'}],  # table names
        [  # columns for users
            {
                'column_name': 'id',
                'data_type': 'int',
                'column_type': 'int(11)',
                'is_nullable': 'NO',
                'column_default': None,
                'column_key': 'PRI',
                'extra': 'auto_increment',
                'column_comment': '',
                'max_length': None,
                'numeric_precision': 10,
                'numeric_scale': 0
            }
        ],
        [{'column_name': 'id'}],  # primary keys
        [],  # foreign keys
        [],  # indexes
        [],  # constraints
        [],  # relationships
    ]
    
    extractor = SchemaExtractor(mock_connector)
    summary = extractor.get_schema_summary()
    
    assert summary['database'] == 'test_db'
    assert summary['db_type'] == 'mysql'
    assert summary['total_tables'] == 1
    assert 'users' in summary['table_names']


def test_clear_cache(mock_connector):
    """Test clearing schema cache"""
    extractor = SchemaExtractor(mock_connector)
    extractor._schema_cache = {"test": "data"}
    
    extractor.clear_cache()
    
    assert extractor._schema_cache is None


def test_format_schema_for_llm(mock_connector):
    """Test formatting schema for LLM"""
    mock_connector.execute_query.side_effect = [
        [{'TABLE_NAME': 'users'}],  # table names
        [  # columns
            {
                'column_name': 'id',
                'data_type': 'int',
                'column_type': 'int(11)',
                'is_nullable': 'NO',
                'column_default': None,
                'column_key': 'PRI',
                'extra': 'auto_increment',
                'column_comment': '',
                'max_length': None,
                'numeric_precision': 10,
                'numeric_scale': 0
            }
        ],
        [{'column_name': 'id'}],  # primary keys
        [],  # foreign keys
        [],  # indexes
        [],  # constraints
        [],  # relationships
    ]
    
    extractor = SchemaExtractor(mock_connector)
    formatted = extractor.format_schema_for_llm()
    
    assert 'Database: test_db' in formatted
    assert 'Table: users' in formatted
    assert 'id: int(11)' in formatted