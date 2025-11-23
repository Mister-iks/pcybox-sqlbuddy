# SQL Buddy 🤖

[![PyPI version](https://badge.fury.io/py/pcybox-sqlbuddy.svg)](https://badge.fury.io/py/pcybox-sqlbuddy)
[![Python Support](https://img.shields.io/pypi/pyversions/pcybox-sqlbuddy.svg)](https://pypi.org/project/pcybox-sqlbuddy/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**AI-powered SQL query generator by [MISTER IKS](https://github.com/Mister-iks)**

Generate accurate SQL queries from natural language using OpenAI GPT or Anthropic Claude. Supports MySQL & PostgreSQL with automatic schema analysis, query validation, and optimization.


## ✨ Key Features

- **Multi-Database**: MySQL & PostgreSQL support
- **Dual AI Support**: OpenAI GPT-4 & Anthropic Claude
- **Built-in Safety**: SQL injection detection & query validation
- **Query Tools**: Generation, explanation, optimization, variations
- **CLI & Library**: Use as Python package or command-line tool
- **Safe by Default**: Validates queries before execution


## 📦 Installation
```bash
pip install pcybox-sqlbuddy
```

### Requirements
- Python 3.8+
- MySQL or PostgreSQL database
- OpenAI API key or Anthropic API key


## 🚀 Quick Start

### Python Library
```python
from sqlbuddy import SQLBuddy

# Using context manager (recommended)
with SQLBuddy(
    db_type="mysql",
    host="localhost",
    user="root",
    password="your_password",
    database="your_db",
    llm_provider="openai",  # or "claude"
    api_key="your_api_key"
) as buddy:
    
    # Generate query from natural language
    result = buddy.generate_query("Show users registered in last 30 days")
    print(result["query"])
    # Output: SELECT * FROM users WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    
    # Generate and execute in one call
    data = buddy.generate_and_execute("Top 10 customers by order value")
    print(data["execution"]["data"])
```

### CLI Usage
```bash
# Test database connection
sqlbuddy test --host localhost --user root --database mydb

# Generate query
sqlbuddy generate "Show all active users" \
  --host localhost --database mydb

# Generate and execute
sqlbuddy generate "Count orders by status" --execute \
  --host localhost --database mydb

# Show database schema
sqlbuddy schema --host localhost --database mydb

# Explain query
sqlbuddy explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 30 DAY"

# Optimize query
sqlbuddy optimize "SELECT * FROM users WHERE email LIKE '%@gmail.com'"
```

## 🔧 Configuration

### Using Environment Variables

Create a `.env` file in your project:
```env
# Database Configuration
SQLBUDDY_DB_TYPE=mysql
SQLBUDDY_DB_HOST=localhost
SQLBUDDY_DB_PORT=3306
SQLBUDDY_DB_USER=root
SQLBUDDY_DB_PASSWORD=your_password
SQLBUDDY_DB_NAME=your_database

# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Then use it:
```python
from sqlbuddy import SQLBuddy
from dotenv import load_dotenv

load_dotenv()

# Environment variables are automatically loaded
buddy = SQLBuddy(llm_provider="openai")
```


## 📖 Usage Examples

### 1. Generate Multiple Query Variations
```python
with SQLBuddy(database="sales_db") as buddy:
    variations = buddy.generate_multiple_queries(
        "Show sales performance by region",
        num_variations=3
    )
    
    for i, var in enumerate(variations, 1):
        print(f"\nApproach {i}:")
        print(var["query"])
```

### 2. Query Optimization
```python
with SQLBuddy(database="analytics") as buddy:
    slow_query = "SELECT * FROM orders WHERE YEAR(created_at) = 2024"
    
    optimization = buddy.optimize_query(slow_query)
    
    print("Original:", optimization["original_query"])
    print("Optimized:", optimization["optimized_query"])
    print("\nDetails:", optimization["optimization_details"])
```

### 3. Query Explanation
```python
with SQLBuddy(database="app_db") as buddy:
    query = """
    SELECT c.name, COUNT(o.id) as order_count
    FROM customers c
    LEFT JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id
    HAVING order_count > 5
    """
    
    explanation = buddy.explain_query(query)
    print(explanation["analysis"])
```

### 4. Schema Exploration
```python
with SQLBuddy(database="ecommerce") as buddy:
    # Get schema summary
    summary = buddy.get_schema_summary()
    print(f"Total Tables: {summary['total_tables']}")
    print(f"Total Relationships: {summary['total_relationships']}")
    
    # Get specific table info
    table_info = buddy.get_table_info("users")
    for col in table_info['columns']:
        print(f"  {col['name']}: {col['type']}")
```

### 5. Safe Query Execution
```python
with SQLBuddy(database="app") as buddy:
    # Generate query
    result = buddy.generate_query("Delete inactive users")
    
    # Check if destructive
    if result["validation"]["is_destructive"]:
        print("⚠️ This is a destructive operation!")
        confirm = input("Continue? (yes/no): ")
        
        if confirm.lower() == "yes":
            exec_result = buddy.execute_query(
                result["query"],
                allow_destructive=True
            )
            print(f"Affected rows: {exec_result['row_count']}")
```


## 🛡️ Security Features

SQL Buddy includes multiple layers of security:

### Automatic Validation
```python
# All queries are validated by default
result = buddy.generate_query("Your description")

# Check validation results
if not result["validation"]["is_valid"]:
    print("Errors:", result["validation"]["errors"])
if result["validation"]["warnings"]:
    print("Warnings:", result["validation"]["warnings"])
```

### Protected Operations

- SQL injection pattern detection
- Destructive operation blocking (DROP, TRUNCATE, DELETE without WHERE)
- Unbalanced parentheses/quotes detection
- Suspicious pattern alerts

### Safe Execution
```python
# Safe by default
buddy.execute_query(query)  # Validated automatically

# Destructive operations need explicit permission
buddy.execute_query(
    "DELETE FROM old_logs",
    allow_destructive=True  # Required for destructive ops
)
```


## 🖥️ CLI Reference

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate SQL from natural language | `sqlbuddy generate "Show active users"` |
| `execute` | Execute SQL query | `sqlbuddy execute "SELECT * FROM users"` |
| `schema` | Show database schema | `sqlbuddy schema --summary` |
| `explain` | Explain SQL query | `sqlbuddy explain "SELECT ..."` |
| `optimize` | Optimize SQL query | `sqlbuddy optimize "SELECT ..."` |
| `test` | Test database connection | `sqlbuddy test --host localhost` |

### Global Options
```bash
--db-type [mysql|postgresql]   Database type (default: mysql)
--host HOST                    Database host
--port PORT                    Database port
--user USER                    Database user
--password PASSWORD            Database password
--database DATABASE            Database name
--llm-provider [openai|claude] LLM provider
--verbose, -v                  Verbose output
```

Use `sqlbuddy COMMAND --help` for command-specific options.


## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
```
Copyright 2025 Ibrahima Khalilou lahi SAMB

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 💼 Commercial Support

Need help integrating SQL Buddy into your project? Looking for custom features or enterprise support?

**I** offer:
- 🎯 Custom development and integration
- 🔒 Security audits and consulting
- 📚 Training and workshops
- ⚡ Priority support
- 🏢 Enterprise licensing

**Contact us:** shadow@pcybox.com

## 📞 Support & Community

- 🐛 [Report a Bug](https://github.com/Mister-iks/sqlbuddy/issues)
- 💡 [Request a Feature](https://github.com/Mister-iks/sqlbuddy/issues)
- 💬 [Discussions](https://github.com/Mister-iks/sqlbuddy/discussions)
- 📧 Email: shadow@pcybox.com
- 🌐 Website: [Coming soon]


## 🙏 Acknowledgments

- Built with ❤️ by [pcybox](https://github.com/Mister-iks)
- Inspired by the need for faster SQL development

---

## ⭐ Star History

If you find SQL Buddy helpful, please consider giving it a star on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=Mister-iks/sqlbuddy&type=Date)](https://star-history.com/#Mister-iks/sqlbuddy&Date)

---

**Made with ❤️ by [IKS](https://github.com/Mister-iks) - Backend Development & Cybersecurity Solutions**
