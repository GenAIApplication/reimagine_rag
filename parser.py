from config import env_config
from llama_cloud_services import LlamaParse
import io
from typing import Optional

parser = LlamaParse(
    api_key=env_config.get("LLAMA_PARSE_API_KEY"),
    parse_mode="parse_page_with_lvm", 
    model="openai-gpt-4-1-mini",
    high_res_ocr=False,             
    adaptive_long_table=True,
    outlined_table_extraction=True,
    output_tables_as_HTML=True,
)


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
