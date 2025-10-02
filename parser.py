from config import env_config
from llama_cloud_services import LlamaParse
import io

parser = LlamaParse(
  # See how to get your API key at https://docs.cloud.llamaindex.ai/api_key
  api_key=env_config.get("LLAMA_PARSE_API_KEY",None),

  # Adaptive long table. LlamaParse will try to detect long table and adapt the output
  adaptive_long_table=True,

  # Whether to try to extract outlined tables
  outlined_table_extraction=True,

  # Whether to use high resolution OCR (Slow)
  high_res_ocr=True,

  # The page separator
  page_separator="\n\n---\n\n",

  # The model to use
  model="openai-gpt-4-1-mini",

  # Whether to output tables as HTML in the markdown output
  output_tables_as_HTML=True,

  # The parsing mode
  parse_mode="parse_page_with_agent",
)

import io
from typing import Optional

async def parse_pdf(pdf_bytes: bytes, file_name: Optional[str] = None):
    """
    Parse a PDF from raw bytes using LlamaParse.

    Args:
        pdf_bytes (bytes): The raw PDF file bytes.
        file_name (str, optional): The name of the PDF file. Defaults to 'uploaded.pdf'.

    Returns:
        ParsedResult: The parsed result from LlamaParse.
    """
    try:
        pdf_stream = io.BytesIO(pdf_bytes)

        # Default file name if not provided
        if not file_name:
            file_name = "uploaded.pdf"

        result = await parser.aparse(
            pdf_stream,
            extra_info={"file_name": file_name}
        )
        return result
    except Exception as e:
        print(f"Error in Parsing PDF Exception: {e}")
        raise
