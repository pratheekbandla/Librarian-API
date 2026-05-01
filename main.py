import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import anthropic

from db import insert_document_sections, search_document_sections

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the embedding model globally so it's loaded only once at startup
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

class AskRequest(BaseModel):
    question: str

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Librarian API!"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Uploaded file must be a PDF."}

    # Save the uploaded file to a temporary file because PyPDFLoader requires a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Load the PDF using LangChain's PyPDFLoader
        loader = PyPDFLoader(temp_file_path)
        docs = loader.load()

        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        # Split the documents into chunks
        chunks = text_splitter.split_documents(docs)

        # Extract text content from the Document objects
        chunk_texts = [chunk.page_content for chunk in chunks]

        if not chunk_texts:
            return {"error": "No text could be extracted from the PDF."}

        # Generate embeddings for the chunks
        embeddings = embedding_model.encode(chunk_texts).tolist()

        # Insert into the database with the original filename
        db_result = insert_document_sections(chunk_texts, embeddings, document_name=file.filename)

        return {
            "total_chunks": len(chunk_texts),
            "db_result": db_result
        }
    except Exception as e:
        print(f"Error during upload processing: {e}")
        return {"error": f"Failed to process document: {str(e)}"}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/ask")
async def ask_question(request: AskRequest):
    if not request.question or not request.question.strip():
        return {"error": "Question cannot be empty."}
        
    try:
        # Generate embedding for the question
        query_embedding = embedding_model.encode([request.question]).tolist()[0]
        
        # Search Supabase for relevant chunks
        results = search_document_sections(query_embedding, match_count=5)
        
        if not results:
            async def empty_response():
                yield f"data: {json.dumps({'chunk': 'I couldn\'t find relevant information in your library.'})}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(empty_response(), media_type="text/event-stream")
        
        # Build context from results
        context_parts = [row.get("content", "") for row in results if "content" in row]
        context = "\n\n---\n\n".join(context_parts)
        
        system_prompt = f"""You are a helpful research assistant called Librarian AI. Answer the user's question using ONLY the context provided below. If the answer is not in the context, say so clearly. Do not make up information.

Context:
{context}
"""
        
        # Initialize Anthropic client
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "Anthropic API key is not configured."}
            
        client = anthropic.AsyncAnthropic(api_key=api_key)
        
        async def stream_generator():
            try:
                # Call Anthropic API with streaming
                async with client.messages.stream(
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": request.question}],
                    model="claude-opus-4-5",
                ) as stream:
                    async for event in stream.text_stream:
                        yield f"data: {json.dumps({'chunk': event})}\n\n"
                
                yield "data: [DONE]\n\n"
            except Exception as e:
                print(f"Error during Anthropic stream: {e}")
                error_msg = f"Sorry, I encountered an error while generating the response: {str(e)}"
                yield f"data: {json.dumps({'chunk': error_msg})}\n\n"
                yield "data: [DONE]\n\n"
                
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    except Exception as e:
        print(f"Error processing ask request: {e}")
        return {"error": f"An error occurred while processing your question: {str(e)}"}
