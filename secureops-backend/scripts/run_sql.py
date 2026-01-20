import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

# Manually load config to avoid import issues if run from scripts dir
from src.core.config import get_config

def run_query(query_str):
    load_dotenv()
    config = get_config()
    
    # Connection logic
    db_config = config.database
    url = f"postgresql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
    
    print(f"Connecting to: {db_config.database}...")
    engine = create_engine(url)
    
    with engine.connect() as conn:
        print(f"Executing: {query_str}\n")
        try:
            result = conn.execute(text(query_str))
            
            # Check if it returns rows (SELECT)
            if result.returns_rows:
                keys = result.keys()
                print(f"| {' | '.join(keys)} |")
                print("-" * (len(str(keys)) + 10))
                
                rows = result.fetchall()
                if not rows:
                    print("(No results)")
                for row in rows:
                    print(f"| {' | '.join(str(val) for val in row)} |")
            else:
                conn.commit()
                print("Statement executed successfully.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_sql.py \"SELECT * FROM ...\"")
        print("Defaulting to: SELECT tablename FROM pg_tables WHERE schemaname='public';")
        run_query("SELECT tablename FROM pg_tables WHERE schemaname='public';")
    else:
        run_query(sys.argv[1])
