"""
Schema extraction module for database structure analysis
"""

from typing import Dict, List, Any, Optional
from sqlbuddy.core.connector import DatabaseConnector


class SchemaExtractor:
    """
    Extracts and analyzes database schema information
    """
    
    def __init__(self, connector: DatabaseConnector):
        """
        Initialize schema extractor
        
        Args:
            connector: DatabaseConnector instance
        """
        self.connector = connector
        self.db_type = connector.db_type
        self._schema_cache = None
    
    def extract_full_schema(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Extract complete database schema
        
        Args:
            use_cache: Use cached schema if available
            
        Returns:
            Dictionary containing complete schema information
        """
        if use_cache and self._schema_cache:
            return self._schema_cache
        
        schema = {
            "database": self.connector.database,
            "db_type": self.db_type,
            "tables": self._extract_tables(),
            "relationships": self._extract_relationships(),
        }
        
        self._schema_cache = schema
        return schema
    
    def _extract_tables(self) -> List[Dict[str, Any]]:
        """
        Extract all tables with their columns, types, and constraints
        
        Returns:
            List of table information dictionaries
        """
        tables = []
        table_names = self._get_table_names()
        
        for table_name in table_names:
            table_info = {
                "name": table_name,
                "columns": self._get_columns(table_name),
                "primary_keys": self._get_primary_keys(table_name),
                "foreign_keys": self._get_foreign_keys(table_name),
                "indexes": self._get_indexes(table_name),
                "constraints": self._get_constraints(table_name),
            }
            tables.append(table_info)
        
        return tables
    
    def _get_table_names(self) -> List[str]:
        """Get all table names in the database"""
        if self.db_type == "mysql":
            query = """
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            params = (self.connector.database,)
        else:  # postgresql
            query = """
                SELECT tablename as table_name
                FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            params = None
        
        results = self.connector.execute_query(query, params)
        return [row['table_name'] if self.db_type == 'postgresql' else row['TABLE_NAME'] 
                for row in results]
    
    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        if self.db_type == "mysql":
            query = """
                SELECT 
                    COLUMN_NAME as column_name,
                    DATA_TYPE as data_type,
                    COLUMN_TYPE as column_type,
                    IS_NULLABLE as is_nullable,
                    COLUMN_DEFAULT as column_default,
                    COLUMN_KEY as column_key,
                    EXTRA as extra,
                    COLUMN_COMMENT as column_comment,
                    CHARACTER_MAXIMUM_LENGTH as max_length,
                    NUMERIC_PRECISION as numeric_precision,
                    NUMERIC_SCALE as numeric_scale
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """
            params = (self.connector.database, table_name)
        else:  # postgresql
            query = """
                SELECT 
                    column_name,
                    data_type,
                    udt_name as column_type,
                    is_nullable,
                    column_default,
                    character_maximum_length as max_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """
            params = (table_name,)
        
        results = self.connector.execute_query(query, params)
        
        columns = []
        for row in results:
            column_info = {
                "name": row['column_name'],
                "type": row['data_type'],
                "full_type": row['column_type'],
                "nullable": row['is_nullable'] == 'YES',
                "default": row['column_default'],
            }
            
            # Add MySQL specific fields
            if self.db_type == "mysql":
                column_info.update({
                    "key": row.get('column_key', ''),
                    "extra": row.get('extra', ''),
                    "comment": row.get('column_comment', ''),
                })
            
            # Add length and precision info
            if row.get('max_length'):
                column_info['max_length'] = row['max_length']
            if row.get('numeric_precision'):
                column_info['numeric_precision'] = row['numeric_precision']
            if row.get('numeric_scale'):
                column_info['numeric_scale'] = row['numeric_scale']
            
            columns.append(column_info)
        
        return columns
    
    def _get_primary_keys(self, table_name: str) -> List[str]:
        """
        Get primary key columns for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of primary key column names
        """
        if self.db_type == "mysql":
            query = """
                SELECT COLUMN_NAME as column_name
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND CONSTRAINT_NAME = 'PRIMARY'
                ORDER BY ORDINAL_POSITION
            """
            params = (self.connector.database, table_name)
        else:  # postgresql
            query = """
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                AND i.indisprimary
                ORDER BY a.attnum
            """
            params = (table_name,)
        
        results = self.connector.execute_query(query, params)
        return [row['column_name'] for row in results]
    
    def _get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get foreign key relationships for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of foreign key information dictionaries
        """
        if self.db_type == "mysql":
            query = """
                SELECT 
                    CONSTRAINT_NAME as constraint_name,
                    COLUMN_NAME as column_name,
                    REFERENCED_TABLE_NAME as referenced_table,
                    REFERENCED_COLUMN_NAME as referenced_column
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s
                AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY ORDINAL_POSITION
            """
            params = (self.connector.database, table_name)
        else:  # postgresql
            query = """
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = 'public'
                AND tc.table_name = %s
            """
            params = (table_name,)
        
        results = self.connector.execute_query(query, params)
        
        foreign_keys = []
        for row in results:
            fk_info = {
                "constraint_name": row['constraint_name'],
                "column": row['column_name'],
                "referenced_table": row['referenced_table'],
                "referenced_column": row['referenced_column'],
            }
            foreign_keys.append(fk_info)
        
        return foreign_keys
    
    def _get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get index information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of index information dictionaries
        """
        if self.db_type == "mysql":
            query = """
                SELECT 
                    INDEX_NAME as index_name,
                    COLUMN_NAME as column_name,
                    NON_UNIQUE as non_unique,
                    SEQ_IN_INDEX as seq_in_index,
                    INDEX_TYPE as index_type
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            params = (self.connector.database, table_name)
        else:  # postgresql
            query = """
                SELECT
                    i.relname as index_name,
                    a.attname as column_name,
                    ix.indisunique::int as non_unique,
                    a.attnum as seq_in_index,
                    am.amname as index_type
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                JOIN pg_am am ON i.relam = am.oid
                WHERE t.relname = %s
                AND t.relkind = 'r'
                ORDER BY i.relname, a.attnum
            """
            params = (table_name,)
        
        results = self.connector.execute_query(query, params)
        
        indexes = []
        for row in results:
            index_info = {
                "name": row['index_name'],
                "column": row['column_name'],
                "unique": row['non_unique'] == 0 if self.db_type == "mysql" else bool(row['non_unique']),
                "type": row.get('index_type', 'BTREE'),
            }
            indexes.append(index_info)
        
        return indexes
    
    def _get_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get constraint information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of constraint information dictionaries
        """
        if self.db_type == "mysql":
            query = """
                SELECT 
                    CONSTRAINT_NAME as constraint_name,
                    CONSTRAINT_TYPE as constraint_type
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            params = (self.connector.database, table_name)
        else:  # postgresql
            query = """
                SELECT
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints AS tc
                WHERE tc.table_schema = 'public' AND tc.table_name = %s
            """
            params = (table_name,)
        
        results = self.connector.execute_query(query, params)
        
        constraints = []
        for row in results:
            constraint_info = {
                "name": row['constraint_name'],
                "type": row['constraint_type'],
            }
            constraints.append(constraint_info)
        
        return constraints
    
    def _extract_relationships(self) -> List[Dict[str, Any]]:
        """
        Extract all relationships between tables
        
        Returns:
            List of relationship information dictionaries
        """
        if self.db_type == "mysql":
            query = """
                SELECT 
                    TABLE_NAME as from_table,
                    COLUMN_NAME as from_column,
                    REFERENCED_TABLE_NAME as to_table,
                    REFERENCED_COLUMN_NAME as to_column,
                    CONSTRAINT_NAME as constraint_name
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """
            params = (self.connector.database,)
        else:  # postgresql
            query = """
                SELECT
                    tc.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column,
                    tc.constraint_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """
            params = None
        
        results = self.connector.execute_query(query, params)
        
        relationships = []
        for row in results:
            relationship = {
                "from_table": row['from_table'],
                "from_column": row['from_column'],
                "to_table": row['to_table'],
                "to_column": row['to_column'],
                "constraint_name": row['constraint_name'],
                "type": "foreign_key"
            }
            relationships.append(relationship)
        
        return relationships
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information dictionary or None if table doesn't exist
        """
        schema = self.extract_full_schema()
        
        for table in schema['tables']:
            if table['name'] == table_name:
                return table
        
        return None
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the database schema
        
        Returns:
            Dictionary with schema summary statistics
        """
        schema = self.extract_full_schema()
        
        total_columns = sum(len(table['columns']) for table in schema['tables'])
        total_foreign_keys = sum(len(table['foreign_keys']) for table in schema['tables'])
        total_indexes = sum(len(table['indexes']) for table in schema['tables'])
        
        return {
            "database": schema['database'],
            "db_type": schema['db_type'],
            "total_tables": len(schema['tables']),
            "total_columns": total_columns,
            "total_relationships": len(schema['relationships']),
            "total_foreign_keys": total_foreign_keys,
            "total_indexes": total_indexes,
            "table_names": [table['name'] for table in schema['tables']]
        }
    
    def format_schema_for_llm(self) -> str:
        """
        Format schema in a human-readable way optimized for LLM consumption
        
        Returns:
            Formatted schema string
        """
        schema = self.extract_full_schema()
        
        output = []
        output.append(f"Database: {schema['database']} ({schema['db_type']})\n")
        output.append("=" * 80)
        output.append("\n")
        
        # Tables and columns
        for table in schema['tables']:
            output.append(f"\nTable: {table['name']}")
            output.append("-" * 40)
            
            # Primary keys
            if table['primary_keys']:
                output.append(f"Primary Key(s): {', '.join(table['primary_keys'])}")
            
            # Columns
            output.append("\nColumns:")
            for col in table['columns']:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] else ""
                output.append(
                    f"  - {col['name']}: {col['full_type']} {nullable}{default}"
                )
            
            # Foreign keys
            if table['foreign_keys']:
                output.append("\nForeign Keys:")
                for fk in table['foreign_keys']:
                    output.append(
                        f"  - {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}"
                    )
            
            # Indexes
            if table['indexes']:
                unique_indexes = [idx for idx in table['indexes'] if idx['unique']]
                if unique_indexes:
                    output.append("\nUnique Indexes:")
                    for idx in unique_indexes:
                        output.append(f"  - {idx['name']} on {idx['column']}")
            
            output.append("\n")
        
        # Relationships summary
        if schema['relationships']:
            output.append("\nRelationships Summary:")
            output.append("-" * 40)
            for rel in schema['relationships']:
                output.append(
                    f"  {rel['from_table']}.{rel['from_column']} → "
                    f"{rel['to_table']}.{rel['to_column']}"
                )
        
        return "\n".join(output)
    
    def clear_cache(self):
        """Clear the cached schema"""
        self._schema_cache = None