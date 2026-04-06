import os
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# ServiceNow Configuration
SNOW_INSTANCE = os.getenv("SNOW_INSTANCE", "dev12345")
SNOW_USER = os.getenv("SNOW_USER", "admin")
SNOW_PASSWORD = os.getenv("SNOW_PASSWORD", "password")
APP_TEAM_GROUP_ID = os.getenv("SNOW_APP_TEAM_GROUP_ID", "YOUR_GROUP_SYS_ID")

def fetch_resolved_incidents():
    """
    Fetches resolved incidents assigned to the application team from ServiceNow.
    """
    url = f"https://{SNOW_INSTANCE}.service-now.com/api/now/table/incident"
    
    # state=6 means Resolved in standard ServiceNow configuration
    query = f"assignment_group={APP_TEAM_GROUP_ID}^state=6"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print(f"Fetching incidents from ServiceNow instance: {SNOW_INSTANCE}...")
    try:
        response = requests.get(
            url, 
            auth=(SNOW_USER, SNOW_PASSWORD), 
            headers=headers, 
            params={"sysparm_query": query, "sysparm_limit": 100}
        )
        response.raise_for_status()
        
        data = response.json()
        incidents = data.get("result", [])
        print(f"Successfully fetched {len(incidents)} resolved incidents.")
        return incidents
    except Exception as e:
        print(f"Error fetching incidents from ServiceNow. (Check your credentials/instance or network): {e}")
        # Return mock data representing typical ServiceNow JSON schema for testing
        print("\n[INFO] Falling back to mock incident data to build the local vector database...")
        return [
            {
                "number": "INC0012345",
                "short_description": "DatabaseTimeoutException during checkout",
                "description": "Application experiencing DatabaseTimeoutException during checkout peak. Connection pool is full.",
                "close_notes": "Increased the MAX_DB_CONNECTIONS in the app_settings table to 200 to handle peak traffic.",
                "cause": "Connection pool size is too low for the current traffic."
            },
            {
                "number": "INC0098765",
                "short_description": "Users locked out of auth-service",
                "description": "Users getting locked out frequently with error User charlie_dev locked out.",
                "close_notes": "Contacted security to whitelist IP; unlocked user manually from database.",
                "cause": "Brute force attempts triggering lock."
            }
        ]

def process_incidents_to_documents(incidents):
    """
    Converts ServiceNow incident JSON objects into LangChain Document objects.
    """
    documents = []
    for inc in incidents:
        # Build a text representation of the incident for the embedding model
        content = f"Incident Number: {inc.get('number', 'UNKNOWN')}\n"
        content += f"Summary: {inc.get('short_description', '')}\n"
        content += f"Error / Issue Description: {inc.get('description', '')}\n"
        content += f"Root Cause: {inc.get('cause', 'Not documented')}\n"
        content += f"Resolution steps: {inc.get('close_notes', '')}\n"
        
        doc = Document(
            page_content=content,
            metadata={
                "id": inc.get("number", "UNKNOWN"),
                "source": "servicenow"
            }
        )
        documents.append(doc)
    return documents

def store_in_vector_db(documents):
    """
    Embeds documents and stores them in a local Chroma Vector Database.
    """
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not set. Cannot generate embeddings.")
        return

    print("Initializing embeddings model...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Store directly into a local directory for our baseline prototype
    persist_directory = "./chroma_db"
    
    print(f"Embedding {len(documents)} documents and saving to Vector DB at {persist_directory}...")
    vectorstore = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=persist_directory
    )
    
    print("ETL Job complete. Knowledge base vector DB is ready!")

if __name__ == "__main__":
    print("====================================")
    print("Starting ServiceNow to Vector DB ETL")
    print("====================================")
    
    incident_records = fetch_resolved_incidents()
    if incident_records:
        langchain_docs = process_incidents_to_documents(incident_records)
        store_in_vector_db(langchain_docs)
