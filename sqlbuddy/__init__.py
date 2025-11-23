"""
SQL Buddy - AI-powered SQL query generator
Copyright (c) 2024 Mister_iks
"""

__version__ = "0.1.0"
__author__ = "Mister_iks"
__email__ = "shadow@pcybox.com"

from sqlbuddy.sqlbuddy import SQLBuddy
from sqlbuddy.core.connector import DatabaseConnector
from sqlbuddy.core.schema_extractor import SchemaExtractor
from sqlbuddy.llm.query_generator import QueryGenerator
from sqlbuddy.utils.validators import QueryValidator
from sqlbuddy.utils.logger import setup_logger

__all__ = [
    "SQLBuddy",
    "DatabaseConnector",
    "SchemaExtractor",
    "QueryGenerator",
    "QueryValidator",
    "setup_logger",
]