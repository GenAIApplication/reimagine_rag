import os
from fastapi import FastAPI
from pydantic import BaseModel
from process_query import QueryProcessor

# Initialize FastAPI app
app = FastAPI(title="Query Processor API", version="1.0.0")

# Initialize QueryProcessor with the same paths from notebook
base_path = os.getcwd()
parsed_results_base = os.path.join(base_path, "parsed_results")
pdf_content_path = os.path.join(parsed_results_base, "pdf_content.json")
chroma_db_path = os.path.join(base_path, "chroma_db")
collection_name = "collection1"

# Initialize processor
processor = QueryProcessor(
    pdf_content_path=pdf_content_path,
    chromadb_path=chroma_db_path,
    collection_name=collection_name,
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query and return the response from the QueryProcessor
    """
    try:
        response = await processor.process_query(query=request.query)
        return QueryResponse(response=response)
    except Exception as e:
        return QueryResponse(response=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
