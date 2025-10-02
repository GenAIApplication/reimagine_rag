
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

embed_model = HuggingFaceEmbedding(model_name="nomic-ai/nomic-embed-text-v1", trust_remote_code=True)