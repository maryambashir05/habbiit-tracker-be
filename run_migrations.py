import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase credentials
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Use service key for migrations
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Missing Supabase credentials")
        
        logger.info("Initializing Supabase client...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # First, create the exec_sql function
        logger.info("Creating exec_sql function...")
        function_path = os.path.join(os.path.dirname(__file__), "migrations", "01_create_function.sql")
        with open(function_path, "r") as f:
            function_sql = f.read()
        
        try:
            # Execute the function creation SQL directly
            supabase._client.postgrest.raw(function_sql)
            logger.info("Function created successfully!")
        except Exception as func_error:
            logger.error(f"Error creating function: {func_error}")
            raise func_error
        
        # Now read and execute the main migration
        logger.info("Reading main migration file...")
        migration_path = os.path.join(os.path.dirname(__file__), "migrations", "setup_database.sql")
        with open(migration_path, "r") as f:
            migration_sql = f.read()
        
        # Execute migration
        logger.info("Executing migration...")
        try:
            # Call the exec_sql function with the migration SQL
            response = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
            logger.info("Migration completed successfully!")
            return True
        except Exception as stmt_error:
            logger.error(f"Error executing migration: {stmt_error}")
            raise stmt_error
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        if hasattr(e, '__dict__'):
            logger.error(f"Error details: {e.__dict__}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    if not success:
        exit(1) 