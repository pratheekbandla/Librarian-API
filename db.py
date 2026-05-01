import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

print(f"DEBUG: URL is '{url}'")

try:
    # Create client conditionally to avoid errors if env vars are missing during import
    supabase: Client | None = create_client(url, key) if url and key else None
except Exception as e:
    print(f"DEBUG: Failed to initialize Supabase client. Error: {e}")
    supabase = None

def insert_document_sections(chunks: list[str], embeddings: list[list[float]], document_name: str) -> dict:
    """
    Inserts a list of text chunks and their corresponding embeddings into the 'document_sections' table.

    Args:
        chunks (list[str]): A list of text chunks.
        embeddings (list[list[float]]): A list of 384-dimension embeddings corresponding to the chunks.
        document_name (str): The name of the document these chunks belong to.

    Returns:
        dict: A response dictionary indicating success or failure.
    """
    if not supabase:
        return {"error": "Supabase client is not initialized. Check your environment variables."}

    if len(chunks) != len(embeddings):
        return {"error": "The number of chunks and embeddings must be equal."}

    # Prepare the data payload for Supabase
    data_to_insert = [
        {"content": chunk, "embedding": embedding, "document_name": document_name}
        for chunk, embedding in zip(chunks, embeddings)
    ]

    try:
        # Perform the insert operation
        # Supabase-py uses .execute() to execute the query
        response = supabase.table("document_sections").insert(data_to_insert).execute()
        
        return {
            "success": True, 
            "inserted_count": len(response.data),
            "data": response.data
    except Exception as e:
        # Handle connection failures, insertion errors, etc.
        print(f"Error inserting into Supabase: {e}")
        return {
            "error": "Failed to insert data into the database.",
            "details": str(e)
        }

def search_document_sections(query_embedding: list[float], match_count: int = 5) -> list[dict]:
    """
    Searches the document_sections table for the closest matching text chunks to the query embedding.
    """
    if not supabase:
        print("Warning: Supabase client not initialized. Returning empty results.")
        return []

    try:
        # Call the Supabase RPC function created in the SQL migration
        response = supabase.rpc(
            "match_document_sections",
            {
                "query_embedding": query_embedding,
                "match_count": match_count
            }
        ).execute()
        
        return response.data
    except Exception as e:
        print(f"Warning: Vector search failed. Error: {e}")
        return []
