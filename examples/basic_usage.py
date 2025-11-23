"""
Basic usage examples for SQL Buddy
"""

from sqlbuddy import SQLBuddy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Basic usage example"""
    print("=" * 80)
    print("Example 1: Basic Query Generation")
    print("=" * 80)
    
    # Initialize SQL Buddy
    buddy = SQLBuddy(
        db_type="mysql",
        host="localhost",
        port=3306,
        user="your_user",
        password="your_password",
        database="your_database",
        llm_provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Generate a query
    result = buddy.generate_query(
        description="Show all users who registered in the last 30 days"
    )
    
    print(f"\nGenerated Query:")
    print(result["query"])
    print(f"\nExplanation:")
    print(result["explanation"])
    
    buddy.disconnect()


def example_with_context_manager():
    """Example using context manager"""
    print("\n" + "=" * 80)
    print("Example 2: Using Context Manager")
    print("=" * 80)
    
    with SQLBuddy(
        db_type="mysql",
        host="localhost",
        user="your_user",
        password="your_password",
        database="your_database",
        llm_provider="openai"
    ) as buddy:
        # Get schema summary
        summary = buddy.get_schema_summary()
        print(f"\nDatabase: {summary['database']}")
        print(f"Total Tables: {summary['total_tables']}")
        print(f"Tables: {', '.join(summary['table_names'])}")
        
        # Generate and execute query
        result = buddy.generate_and_execute(
            description="Count the total number of users"
        )
        
        print(f"\nQuery: {result['generation']['query']}")
        print(f"Result: {result['execution']['data']}")


def example_multiple_variations():
    """Example generating multiple query variations"""
    print("\n" + "=" * 80)
    print("Example 3: Multiple Query Variations")
    print("=" * 80)
    
    with SQLBuddy(
        db_type="mysql",
        host="localhost",
        user="your_user",
        password="your_password",
        database="your_database"
    ) as buddy:
        variations = buddy.generate_multiple_queries(
            description="Find users with the most orders",
            num_variations=3
        )
        
        for i, var in enumerate(variations, 1):
            print(f"\n--- Variation {i} ---")
            print(var["query"])


def example_explain_and_optimize():
    """Example explaining and optimizing queries"""
    print("\n" + "=" * 80)
    print("Example 4: Explain and Optimize")
    print("=" * 80)
    
    with SQLBuddy(
        db_type="mysql",
        host="localhost",
        user="your_user",
        password="your_password",
        database="your_database"
    ) as buddy:
        query = "SELECT * FROM users WHERE email LIKE '%@example.com'"
        
        # Explain query
        explanation = buddy.explain_query(query)
        print(f"\nExplanation:")
        print(explanation["analysis"])
        
        # Optimize query
        optimization = buddy.optimize_query(query)
        print(f"\nOptimized Query:")
        print(optimization["optimized_query"])


if __name__ == "__main__":
    # Run examples (comment out as needed)
    # example_basic_usage()
    # example_with_context_manager()
    # example_multiple_variations()
    # example_explain_and_optimize()
    
    print("\n" + "=" * 80)
    print("To run these examples, update the database credentials")
    print("and uncomment the example you want to run")
    print("=" * 80)