import os
from supabase import create_client
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Service role key
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Anon key

logger.debug(f"SUPABASE_URL: {SUPABASE_URL}")
logger.debug(f"SUPABASE_KEY: {SUPABASE_KEY[:10]}...")
logger.debug(f"SUPABASE_ANON_KEY: {SUPABASE_ANON_KEY[:10]}...")

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_ANON_KEY:
    logger.error("Supabase credentials not found in environment variables")
    raise ValueError("SUPABASE_URL, SUPABASE_KEY, and SUPABASE_ANON_KEY must be set in environment variables")

try:
    # Initialize Supabase clients
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)  # Admin client
    supabase_anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)  # Anonymous client
    logger.info("Supabase clients initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase clients: {str(e)}")
    raise 