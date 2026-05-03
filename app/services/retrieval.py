from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


KEYWORD_TO_FILE = {
    "refund": "return_policy.md",
    "return": "return_policy.md",
    "shipping": "shipping_policy.md",
    "track": "shipping_policy.md",
    "address": "address_change_policy.md",
    "escalat": "escalation_policy.md",
}


class PolicyRetriever:
    """Semantic search for policy documents using FAISS."""
    
    def __init__(self):
        self.settings = get_settings()
        self.index = None
        self.documents = []
        self.embeddings_model = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of FAISS index."""
        if self._initialized:
            return
        
        index_path = Path(self.settings.VECTOR_INDEX_DIR)
        index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings model
        if self.settings.DEEPSEEK_API_KEY:
            self.embeddings_model = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                api_key=self.settings.DEEPSEEK_API_KEY,
            )
        
        # Try to load existing index
        faiss_path = index_path / "policy_index.faiss"
        docs_path = index_path / "policy_docs.pkl"
        
        if faiss_path.exists() and docs_path.exists():
            try:
                self.index = faiss.read_index(str(faiss_path))
                self.documents = pickle.loads(docs_path.read_bytes())
                self._initialized = True
                return
            except Exception:
                pass  # Rebuild index if loading fails
        
        # Build new index
        self._build_index()
        self._initialized = True
    
    def _build_index(self):
        """Build FAISS index from policy documents."""
        kb_path = Path("data/knowledge_base")
        documents = []
        
        for md_file in kb_path.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            # Split into chunks for better retrieval
            chunks = self._split_into_chunks(content, chunk_size=500)
            for i, chunk in enumerate(chunks):
                documents.append({
                    "source": md_file.name,
                    "content": chunk,
                    "chunk_id": i,
                })
        
        self.documents = documents
        
        if not self.embeddings_model or not documents:
            # Fallback: no embeddings available
            return
        
        # Create embeddings
        texts = [doc["content"] for doc in documents]
        embeddings = self.embeddings_model.embed_documents(texts)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Build FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        # Save index and documents
        index_path = Path(self.settings.VECTOR_INDEX_DIR)
        faiss.write_index(self.index, str(index_path / "policy_index.faiss"))
        (index_path / "policy_docs.pkl").write_bytes(pickle.dumps(documents))
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> list[str]:
        """Split text into smaller chunks for better retrieval."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [text]
    
    def search(self, query: str, k: int = 3) -> dict[str, str]:
        """Search for relevant policy content."""
        self._initialize()
        
        # Fallback to keyword matching if no index
        if not self.index or not self.embeddings_model:
            return self._keyword_fallback(query)
        
        try:
            # Create query embedding
            query_embedding = self.embeddings_model.embed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Search
            distances, indices = self.index.search(query_array, k)
            
            # Combine top-k results
            results = []
            for idx in indices[0]:
                if idx < len(self.documents):
                    results.append(self.documents[idx])
            
            if results:
                combined_content = "\n\n---\n\n".join(r["content"] for r in results)
                sources = list(set(r["source"] for r in results))
                return {
                    "source": ", ".join(sources),
                    "content": combined_content,
                }
        except Exception:
            pass  # Fallback to keyword matching
        
        return self._keyword_fallback(query)
    
    def _keyword_fallback(self, query: str) -> dict[str, str]:
        """Fallback to keyword-based retrieval."""
        lowered_query = query.lower()
        selected_file = "shipping_policy.md"
        for keyword, file_name in KEYWORD_TO_FILE.items():
            if keyword in lowered_query:
                selected_file = file_name
                break
        
        path = Path("data/knowledge_base") / selected_file
        return {"source": selected_file, "content": path.read_text(encoding="utf-8")}


# Global retriever instance
_retriever: PolicyRetriever | None = None


def get_retriever() -> PolicyRetriever:
    """Get or create global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = PolicyRetriever()
    return _retriever


def retrieve_policy_context(query: str) -> dict[str, str]:
    """Retrieve relevant policy context using semantic search with caching."""
    from app.services.cache import get_policy_cache
    
    cache = get_policy_cache()
    query_hash = cache.get_query_hash(query)
    
    # Try cache first
    cached_result = cache.get_policy(query_hash)
    if cached_result:
        return cached_result
    
    # Retrieve using semantic search
    retriever = get_retriever()
    result = retriever.search(query)
    
    # Cache result
    cache.set_policy(query_hash, result)
    
    return result
