import os
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain

# --- 1. Database Tool (Text-to-SQL) ---
# Assuming local MySQL database is set up as per docker-compose.yml
DB_USER = "agent"
DB_PASS = "agentpassword"
DB_HOST = "localhost" # Adjust if running docker remotely
DB_NAME = "support_db"

def get_db_connection():
    # Use pymysql driver
    db_uri = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"
    try:
        db = SQLDatabase.from_uri(db_uri)
        return db
    except Exception as e:
        print(f"Warning: Could not connect to the database. Error: {e}")
        return None

db_instance = get_db_connection()

@tool
def query_application_database(query_description: str) -> str:
    """Useful for querying the application database to find user statuses, application configurations, etc. 
    Input should be a description of what you want to know."""
    if not db_instance:
        return "Error: Database is not connected."
    
    # In a real scenario we'd use create_sql_query_chain to formulate sql, then execute.
    # For a simple mockup or if you prefer a pre-built toolkit use SQLDatabaseToolkit.
    # Here we show a mocked response demonstrating the workflow since LangChain's SQL chain requires an LLM instance to run dynamically inside the tool.
    return "MOCK SQL DB RESULT: [{'username': 'alice_admin', 'status': 'active'}, {'username': 'charlie_dev', 'status': 'locked'}]"

# --- 2. AWS CloudWatch Logs Mock Tool ---
@tool
def fetch_cloudwatch_error_logs(timeframe_hours: int) -> str:
    """Useful to fetch recent ERROR level logs from AWS CloudWatch for the application. 
    Input should be integer hours to look back."""
    
    mock_logs = f"""
    [timestamp: 2024-05-11 08:30:15] [ERROR] [checkout-service] Exception: DatabaseTimeoutException - Connection pool exhausted.
    [timestamp: 2024-05-11 09:05:10] [ERROR] [auth-service] User charlie_dev locked out.
    """
    return f"Logs from the last {timeframe_hours} hours:\n{mock_logs}"

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# --- 3. ServiceNow Knowledge Base Tool (RAG) ---
@tool
def search_servicenow_knowledge_base(error_message: str) -> str:
    """Useful to find historical ServiceNow incidents and known solutions for a given error message or exception trace.
    Input should be the specific error message text."""
    
    persist_directory = "./chroma_db"
    
    if os.path.exists(persist_directory) and os.getenv("OPENAI_API_KEY"):
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
            docs = vectorstore.similarity_search(error_message, k=2)
            if docs:
                return "Found relevant historical incidents in Vector DB:\n\n" + "\n---\n".join([d.page_content for d in docs])
        except Exception as e:
            print(f"[Warning] Failed to query vector DB: {e}")
            
    # Fallback: Simulating a Vector DB semantic search if DB doesn't exist
    print("[Warning] chroma_db not found or error occurred. Falling back to mock RAG mode.")
    error_message_lower = error_message.lower()
    
    if "databasetimeoutexception" in error_message_lower or "connection pool" in error_message_lower:
        return """
        FOUND INCIDENT: INC0012345
        Description: Application experiencing DatabaseTimeoutException during checkout peak.
        Root Cause: Connection pool size is too low for the current traffic.
        Resolution: Increase the MAX_DB_CONNECTIONS in the app_settings table to 200 or scale up the DB instance.
        """
    elif "locked out" in error_message_lower:
        return """
        FOUND INCIDENT: INC0098765
        Description: Users getting locked out frequently.
        Root Cause: Brute force attempts triggering lock.
        Resolution: Contact security to whitelist IP or unlock user from database using support scripts.
        """
    else:
        return "No relevant historical incidents found in the ServiceNow Knowledge Base."

# Assemble tools list
agent_tools = [
    query_application_database,
    fetch_cloudwatch_error_logs,
    search_servicenow_knowledge_base
]
