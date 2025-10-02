import json
import pandas as pd
import os
import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.schema import TextNode
from llama_index.core import StorageContext
from get_embedding_model import embed_model




def extract_pdf_content(pdf_result: dict, pdf_content_path: str) -> dict:
    """
    Extract text and markdown content from a PDF parsing result.
    
    Args:
        pdf_result (dict): The parsed JSON result from the PDF.
        
    Returns:
        dict: A dictionary with page-wise content containing:
            - 'text_only': concatenated plain text.
            - 'full_page_markdown': markdown including tables and formatting.
    """
    page_content_map = {}

    for page_idx, page in enumerate(pdf_result.get("pages", [])):
        page_key = page.get("page")
        page_content_map[page_key] = {
            "text_only": "",
            "full_page_markdown": ""
        }

        items = page.get("items", [])
        text_accumulator = ""
        markdown_accumulator = ""

        for item in items:
            item_type = item.get("type", "").lower()
            if item_type == "table":
                rows = item.get("rows")
                if rows:
                    try:
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        table_md = df.to_markdown(index=False)
                        markdown_accumulator += table_md + "\n"
                    except Exception as e:
                        print(f"Error processing table on {page_key}: {e}")
            else:
                md_content = item.get("md", "")
                markdown_accumulator += md_content + "\n"
                text_accumulator += md_content + "\n"

        page_content_map[page_key]["text_only"] = text_accumulator.strip()
        page_content_map[page_key]["full_page_markdown"] = markdown_accumulator.strip()
    
    if pdf_content_path:
        try:
            os.makedirs(os.path.dirname(pdf_content_path), exist_ok=True)
            with open(pdf_content_path, "w", encoding="utf-8") as f:
                json.dump(page_content_map, f, indent=4, ensure_ascii=False)
            print(f"Content saved to {pdf_content_path}")
        except Exception as e:
            print(f"Error saving content to {pdf_content_path}: {e}")

    return page_content_map


def chunk_text(text, chunk_size=1000, overlap=300):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # move start pointer with overlap
    return chunks

def create_nodes(page_wise_content:dict):
    nodes = []
    for pg_no, content in page_wise_content.items():
        text_only_part = content.get("text_only", "")
        
        if text_only_part:
            words_count = len(text_only_part.split())
            
            if words_count > 1000:
                # chunk text
                chunks = chunk_text(text_only_part, chunk_size=1000, overlap=300)
                for i, chunk in enumerate(chunks):
                    nodes.append(
                        TextNode(
                            text=chunk,
                            metadata={
                                "page_no": pg_no,
                            }
                        )
                    )
            else:
                nodes.append(
                    TextNode(
                        text=text_only_part,
                        metadata={"page_no": pg_no}
                    )
                )
    return nodes

def create_vector_index_from_nodes(nodes:list,chromadb_path:str,collection_name:str):
    db = chromadb.PersistentClient(path=chromadb_path)
    chroma_collection = db.create_collection(name=collection_name, get_or_create=True)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)


def generate_vector_index(pdf_result: dict, chromadb_path:str,collection_name:str, pdf_content_path: str = None):
    page_content_map = extract_pdf_content(pdf_result,pdf_content_path)
    nodes = create_nodes(page_content_map)
    create_vector_index_from_nodes(nodes,chromadb_path,collection_name)

def get_index(chromadb_path:str,collection_name:str):
    db2 = chromadb.PersistentClient(path=chromadb_path)
    chroma_collection = db2.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )
    return index

def get_retriever(chromadb_path:str,collection_name:str):
    index = get_index(chromadb_path,collection_name)
    retriever = index.as_retriever(
    search_kwargs={
        "similarity_top_k": 3,   # number of most similar nodes
        "include_text": False,    # whether to return the node text
    }
    )
    return retriever





    
