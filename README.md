# SQL Buddy 🤖

[![PyPI version](https://badge.fury.io/py/pcybox-sqlbuddy.svg)](https://badge.fury.io/py/pcybox-sqlbuddy)
[![Python Support](https://img.shields.io/pypi/pyversions/sqlbuddy.svg)](https://test.pypi.org/project/pcybox-sqlbuddy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


**AI-powered SQL query generator by [Mister_iks](https://github.com/Mister-iks)**

Generate accurate SQL queries from natural language using OpenAI or Claude. Supports MySQL & PostgreSQL with automatic schema analysis, query validation, and optimization.

## ✨ Key Features

- 🔌 **Multi-Database**: MySQL & PostgreSQL
- 🧠 **Dual AI Support**: OpenAI GPT-4 & Anthropic Claude
- 🔍 **Smart Schema Analysis**: Automatic table/relationship detection
- ✅ **Built-in Safety**: SQL injection detection & query validation
- 💡 **Query Tools**: Generation, explanation, optimization, variations
- 🖥️ **CLI & Library**: Use as Python package or command-line tool

## 📦 Installation
```bash
pip install pcybox-sqlbuddy
```

## 🚀 Quick Start

### Python Library
```python
from sqlbuddy import SQLBuddy

with SQLBuddy(
    db_type="mysql",
    host="localhost",
    user="root",
    password="your_password",
    database="your_db",
    llm_provider="openai",
    api_key="your_api_key"
) as buddy:
    # Generate query
    result = buddy.generate_query("Show users registered in last 30 days")
    print(result["query"])
    
    # Execute directly
    data = buddy.generate_and_execute("Top 10 customers by order value")
    print(data["execution"]["data"])
```

### CLI
```bash
# Generate query
sqlbuddy generate "Show all active users" --host localhost --database mydb

# Generate and execute
sqlbuddy generate "Count orders by status" --execute --database mydb

# Explain query
sqlbuddy explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 30 DAY"

# Optimize query
sqlbuddy optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"
```

## 🔧 Configuration

Create `.env` file:
```env
SQLBUDDY_DB_TYPE=mysql
SQLBUDDY_DB_HOST=localhost
SQLBUDDY_DB_USER=root
SQLBUDDY_DB_PASSWORD=your_password
SQLBUDDY_DB_NAME=your_database

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 📖 Common Use Cases

### Generate Multiple Variations
```python
variations = buddy.generate_multiple_queries(
    "Show sales by region",
    num_variations=3
)
```

### Query Optimization
```python
optimization = buddy.optimize_query("SELECT * FROM orders WHERE YEAR(created_at) = 2024")
print(optimization["optimized_query"])
```

### Schema Exploration
```python
summary = buddy.get_schema_summary()
table_info = buddy.get_table_info("users")
```

## 🛡️ Security

- Automatic SQL injection detection
- Destructive operation protection
- Query validation enabled by default
- Safe execution mode
```python
# Destructive ops require explicit permission
buddy.execute_query("DELETE FROM old_logs", allow_destructive=True)
```

## 🖥️ CLI Commands

| Command | Description |
|---------|-------------|
| `generate` | Generate SQL from natural language |
| `execute` | Execute SQL query |
| `schema` | Show database schema |
| `explain` | Explain SQL query |
| `optimize` | Optimize SQL query |
| `test` | Test database connection |

Use `--help` with any command for options.

## 🧪 Testing
```bash
pytest                          # Run all tests
pytest --cov=sqlbuddy          # With coverage
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 📞 Support

- 🐛 [Report Bug](https://github.com/Mister-iks/pcybox-sqlbuddy/issues)
- 💡 [Feature Request](https://github.com/Mister-iks/pcybox-sqlbuddy/issues)
- 📧 shadow@pcybox.com

---

**Made with ❤️ by [Mister__iks](https://github.com/pcybox) - Backend Development & Cybersecurity Solutions**