"""
Pcybox SQLBuddy - AI-powered SQL query generator
Copyright (c) 2025 Ibrahima Khalilou Lahi SAMB (pcybox)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__version__ = "0.1.0"
__author__ = "Ibrahima Khalilou Lahi SAMB"
__email__ = "shadow@pcybox.com"
__license__ = "Apache-2.0"

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