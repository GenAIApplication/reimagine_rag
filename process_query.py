from urllib3 import response
from indexing import get_retriever
from create_client import get_client
from google.genai import types
import json
import time
from system_prompts import pdfQuerySystemPrompt



class QueryProcessor:
    def __init__(self, pdf_content_path, chromadb_path, collection_name):
        self.pdf_content_path = pdf_content_path
        self.chromadb_path = chromadb_path
        self.collection_name = collection_name
        
        # Load JSON as a Python dict
        with open(self.pdf_content_path, "r", encoding="utf-8") as f:
            self.pdf_content_result = json.load(f)
        
        self.pdf_content_result = {int(k): v for k, v in self.pdf_content_result.items()}
        
        # Initialize retriever
        self.retriever = get_retriever(self.chromadb_path, self.collection_name)

    def get_content(self, query: str):
        results = self.retriever.retrieve(query)
        page_numbers = set()
        for result in results:
            page_numbers.add(result.metadata.get('page_no'))
        contents = {}
        for pg_no in page_numbers:
            page_content = self.pdf_content_result.get(pg_no, None)
            if page_content:
                contents[pg_no] = page_content.get("full_page_markdown")
        sorted_contents = {k:contents[k] for k in sorted(contents)}
        return sorted_contents

    def create_gemini_contents(self, pdf_content:dict, query:str):
        contents = []
        context = f"User Question: - {query}\n"
        for pg_no,content in pdf_content.items():
            context+=f"Page Number - {pg_no}\n{content}\n"
        contents.append(context)
        return contents

    async def get_gemini_response(self, contents, max_retries=3, base_delay=1):
        """
        Calls Gemini API with up to max_retries and exponential backoff.
        """
        client = get_client()
        attempt = 0

        while attempt < max_retries:
            try:
                response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=pdfQuerySystemPrompt,
                        temperature=0.0,
                        thinking_config=types.ThinkingConfig(thinking_budget=-1),
                    ),
                    contents=contents
                )
                return response.text

            except Exception as e:
                attempt += 1
                if attempt == max_retries:
                    raise  
                delay = base_delay * (2 ** (attempt - 1)) 
                print(f"Attempt {attempt} failed. Error -  {e}. Retrying in {delay}s")
                time.sleep(delay)


    async def process_query(self, query: str):
        pdf_content = self.get_content(query)
        gemini_content = self.create_gemini_contents(pdf_content,query)
        response = await self.get_gemini_response(gemini_content)
        return response