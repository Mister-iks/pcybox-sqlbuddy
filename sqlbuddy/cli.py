"""
Command-line interface for SQL Buddy
"""

import argparse
import sys
import os
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
from sqlbuddy import SQLBuddy
import logging


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI"""
    parser = argparse.ArgumentParser(
        description="SQL Buddy - AI-powered SQL query generator by pcybox",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a query
  sqlbuddy generate "Show all users registered in last 30 days" \\
    --host localhost --user root --database mydb

  # Execute generated query
  sqlbuddy generate "Count users by country" --execute \\
    --host localhost --user root --database mydb

  # Show database schema
  sqlbuddy schema --host localhost --user root --database mydb

  # Explain a query
  sqlbuddy explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 30 DAY"

Environment variables:
  SQLBUDDY_DB_HOST      Database host
  SQLBUDDY_DB_PORT      Database port
  SQLBUDDY_DB_USER      Database user
  SQLBUDDY_DB_PASSWORD  Database password
  SQLBUDDY_DB_NAME      Database name
  SQLBUDDY_DB_TYPE      Database type (mysql or postgresql)
  OPENAI_API_KEY        OpenAI API key
  ANTHROPIC_API_KEY     Anthropic API key
        """
    )
    
    # Database connection options
    db_group = parser.add_argument_group('Database Connection')
    db_group.add_argument('--db-type', default=os.getenv('SQLBUDDY_DB_TYPE', 'mysql'),
                         choices=['mysql', 'postgresql'],
                         help='Database type (default: mysql)')
    db_group.add_argument('--host', default=os.getenv('SQLBUDDY_DB_HOST', 'localhost'),
                         help='Database host')
    db_group.add_argument('--port', type=int, default=os.getenv('SQLBUDDY_DB_PORT'),
                         help='Database port')
    db_group.add_argument('--user', default=os.getenv('SQLBUDDY_DB_USER', ''),
                         help='Database user')
    db_group.add_argument('--password', default=os.getenv('SQLBUDDY_DB_PASSWORD', ''),
                         help='Database password')
    db_group.add_argument('--database', default=os.getenv('SQLBUDDY_DB_NAME', ''),
                         help='Database name')
    
    # LLM options
    llm_group = parser.add_argument_group('LLM Configuration')
    llm_group.add_argument('--llm-provider', default='openai',
                          choices=['openai', 'claude'],
                          help='LLM provider (default: openai)')
    llm_group.add_argument('--api-key', help='API key for LLM provider')
    llm_group.add_argument('--model', help='Specific model to use')
    llm_group.add_argument('--temperature', type=float, default=0.1,
                          help='Temperature for generation (default: 0.1)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate SQL query from description')
    generate_parser.add_argument('description', help='Natural language description of the query')
    generate_parser.add_argument('--execute', action='store_true',
                                help='Execute the generated query')
    generate_parser.add_argument('--variations', type=int, default=1,
                                help='Number of query variations to generate')
    generate_parser.add_argument('--no-validate', action='store_true',
                                help='Skip query validation')
    
    # Execute command
    execute_parser = subparsers.add_parser('execute', help='Execute a SQL query')
    execute_parser.add_argument('query', help='SQL query to execute')
    execute_parser.add_argument('--no-validate', action='store_true',
                               help='Skip query validation')
    execute_parser.add_argument('--allow-destructive', action='store_true',
                               help='Allow destructive operations')
    
    # Schema command
    schema_parser = subparsers.add_parser('schema', help='Show database schema')
    schema_parser.add_argument('--table', help='Show schema for specific table only')
    schema_parser.add_argument('--summary', action='store_true',
                              help='Show only schema summary')
    
    # Explain command
    explain_parser = subparsers.add_parser('explain', help='Explain a SQL query')
    explain_parser.add_argument('query', help='SQL query to explain')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize a SQL query')
    optimize_parser.add_argument('query', help='SQL query to optimize')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test database connection')
    
    # General options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--version', action='version',
                       version='SQL Buddy 0.1.0 by pcybox')
    
    return parser


def handle_generate_command(buddy: SQLBuddy, args) -> int:
    """Handle generate command"""
    try:
        validate = not args.no_validate
        
        if args.variations > 1:
            console.print(f"\n[bold cyan]Generating {args.variations} query variations...[/bold cyan]\n")
            variations = buddy.generate_multiple_queries(
                description=args.description,
                num_variations=args.variations,
                validate=validate
            )
            
            for i, var in enumerate(variations, 1):
                if "error" in var:
                    console.print(f"[bold red]Variation {i} failed:[/bold red] {var['error']}")
                    continue
                
                console.print(f"\n[bold yellow]Variation {i}:[/bold yellow]")
                syntax = Syntax(var["query"], "sql", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=f"Generated Query {i}"))
                
                if var.get("explanation"):
                    console.print(f"\n[italic]{var['explanation']}[/italic]")
                
                if args.execute:
                    console.print(f"\n[bold cyan]Executing variation {i}...[/bold cyan]")
                    result = buddy.execute_query(var["query"], validate=validate)
                    display_execution_result(result)
        
        else:
            console.print("\n[bold cyan]Generating query...[/bold cyan]\n")
            result = buddy.generate_query(
                description=args.description,
                validate=validate
            )
            
            # Display query
            syntax = Syntax(result["query"], "sql", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title="Generated Query"))
            
            # Display explanation
            if result.get("explanation"):
                console.print(f"\n[bold]Explanation:[/bold]")
                console.print(result["explanation"])
            
            # Display tables used
            if result.get("tables_used"):
                console.print(f"\n[bold]Tables Used:[/bold] {', '.join(result['tables_used'])}")
            
            # Display validation
            if result.get("validation"):
                validation = result["validation"]
                if validation["errors"]:
                    console.print(f"\n[bold red]Validation Errors:[/bold red]")
                    for error in validation["errors"]:
                        console.print(f"  • {error}")
                if validation["warnings"]:
                    console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
                    for warning in validation["warnings"]:
                        console.print(f"  • {warning}")
            
            # Execute if requested
            if args.execute:
                console.print("\n[bold cyan]Executing query...[/bold cyan]\n")
                exec_result = buddy.execute_query(result["query"], validate=validate)
                display_execution_result(exec_result)
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def display_execution_result(result: dict):
    """Display query execution result"""
    if result["success"]:
        console.print(f"[bold green]✓ Query executed successfully[/bold green]")
        console.print(f"Rows affected/returned: {result['row_count']}")
        
        if result["data"]:
            # Display results in table
            if len(result["data"]) > 0:
                table = Table(show_header=True, header_style="bold magenta")
                
                # Add columns
                for key in result["data"][0].keys():
                    table.add_column(str(key))
                
                # Add rows (limit to first 50)
                for row in result["data"][:50]:
                    table.add_row(*[str(v) for v in row.values()])
                
                console.print("\n")
                console.print(table)
                
                if len(result["data"]) > 50:
                    console.print(f"\n[italic]Showing first 50 of {len(result['data'])} rows[/italic]")
    else:
        console.print(f"[bold red]✗ Query execution failed[/bold red]")
        console.print(f"Error: {result['error']}")


def handle_execute_command(buddy: SQLBuddy, args) -> int:
    """Handle execute command"""
    try:
        validate = not args.no_validate
        
        console.print("\n[bold cyan]Executing query...[/bold cyan]\n")
        result = buddy.execute_query(
            query=args.query,
            validate=validate,
            allow_destructive=args.allow_destructive
        )
        
        display_execution_result(result)
        return 0 if result["success"] else 1
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def handle_schema_command(buddy: SQLBuddy, args) -> int:
    """Handle schema command"""
    try:
        if args.summary:
            summary = buddy.get_schema_summary()
            
            console.print("\n[bold cyan]Database Schema Summary[/bold cyan]\n")
            console.print(f"Database: {summary['database']}")
            console.print(f"Type: {summary['db_type']}")
            console.print(f"Total Tables: {summary['total_tables']}")
            console.print(f"Total Columns: {summary['total_columns']}")
            console.print(f"Total Relationships: {summary['total_relationships']}")
            console.print(f"\n[bold]Tables:[/bold]")
            for table in summary['table_names']:
                console.print(f"  • {table}")
        
        elif args.table:
            table_info = buddy.get_table_info(args.table)
            if not table_info:
                console.print(f"[bold red]Table '{args.table}' not found[/bold red]")
                return 1
            
            console.print(f"\n[bold cyan]Table: {args.table}[/bold cyan]\n")
            
            # Columns
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Column")
            table.add_column("Type")
            table.add_column("Nullable")
            table.add_column("Default")
            
            for col in table_info['columns']:
                table.add_row(
                    col['name'],
                    col['full_type'],
                    "Yes" if col['nullable'] else "No",
                    str(col['default']) if col['default'] else ""
                )
            
            console.print(table)
            
            # Primary keys
            if table_info['primary_keys']:
                console.print(f"\n[bold]Primary Keys:[/bold] {', '.join(table_info['primary_keys'])}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                console.print(f"\n[bold]Foreign Keys:[/bold]")
                for fk in table_info['foreign_keys']:
                    console.print(f"  • {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}")
        
        else:
            schema_formatted = buddy.schema_extractor.format_schema_for_llm()
            console.print("\n[bold cyan]Database Schema[/bold cyan]\n")
            console.print(schema_formatted)
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def handle_explain_command(buddy: SQLBuddy, args) -> int:
    """Handle explain command"""
    try:
        console.print("\n[bold cyan]Analyzing query...[/bold cyan]\n")
        result = buddy.explain_query(args.query)
        
        syntax = Syntax(result["query"], "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Query"))
        
        console.print("\n[bold]Analysis:[/bold]")
        console.print(result["analysis"])
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def handle_optimize_command(buddy: SQLBuddy, args) -> int:
    """Handle optimize command"""
    try:
        console.print("\n[bold cyan]Optimizing query...[/bold cyan]\n")
        result = buddy.optimize_query(args.query)
        
        console.print("[bold]Original Query:[/bold]")
        syntax = Syntax(result["original_query"], "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax))
        
        console.print("\n[bold]Optimized Query:[/bold]")
        syntax = Syntax(result["optimized_query"], "sql", theme="monokai", line_numbers=True)
        console.print(Panel(syntax))
        
        console.print("\n[bold]Optimization Details:[/bold]")
        console.print(result["optimization_details"])
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def handle_test_command(buddy: SQLBuddy, args) -> int:
    """Handle test command"""
    try:
        console.print("\n[bold cyan]Testing database connection...[/bold cyan]\n")
        result = buddy.connect()
        
        if result["success"]:
            console.print("[bold green]✓ Connection successful[/bold green]")
            console.print(f"\nDatabase: {result['database']}")
            console.print(f"Type: {result['db_type']}")
            if result.get('server_info'):
                console.print(f"\nServer Info:")
                for key, value in result['server_info'].items():
                    console.print(f"  {key}: {value}")
            return 0
        else:
            console.print(f"[bold red]✗ Connection failed[/bold red]")
            console.print(f"Error: {result['message']}")
            return 1
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1


def main():
    """Main CLI entry point"""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    try:
        # Initialize SQL Buddy
        buddy = SQLBuddy(
            db_type=args.db_type,
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            llm_provider=args.llm_provider,
            api_key=args.api_key,
            llm_model=args.model,
            temperature=args.temperature,
            auto_connect=(args.command != 'test'),
            log_level=log_level
        )
        
        # Route to command handler
        if args.command == 'generate':
            return handle_generate_command(buddy, args)
        elif args.command == 'execute':
            return handle_execute_command(buddy, args)
        elif args.command == 'schema':
            return handle_schema_command(buddy, args)
        elif args.command == 'explain':
            return handle_explain_command(buddy, args)
        elif args.command == 'optimize':
            return handle_optimize_command(buddy, args)
        elif args.command == 'test':
            return handle_test_command(buddy, args)
        else:
            parser.print_help()
            return 0
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())