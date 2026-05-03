from __future__ import annotations

import pickle
from pathlib import Path

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


KEYWORD_TO_FILE = {
    # Return & Refund
    "refund": "return_policy.md",
    "return": "return_policy.md",
    "money back": "return_policy.md",
    "damaged": "return_policy.md",
    "defective": "warranty_policy.md",
    "warranty": "warranty_policy.md",
    
    # Shipping & Tracking
    "shipping": "shipping_policy.md",
    "track": "shipping_policy.md",
    "delivery": "shipping_policy.md",
    "out for delivery": "shipping_policy.md",
    "shipped": "shipping_policy.md",
    "international": "shipping_policy.md",
    
    # Address
    "address": "address_change_policy.md",
    "shipping address": "address_change_policy.md",
    "delivery address": "address_change_policy.md",
    
    # Cancellation
    "cancel": "cancellation_policy.md",
    "cancellation": "cancellation_policy.md",
    
    # Payment
    "payment": "payment_policy.md",
    "pay": "payment_policy.md",
    "credit card": "payment_policy.md",
    "paypal": "payment_policy.md",
    "charge": "payment_policy.md",
    
    # Support
    "escalat": "escalation_policy.md",
    "human": "support_policy.md",
    "agent": "support_policy.md",
    "support": "support_policy.md",
    "contact": "support_policy.md",
    "phone": "support_policy.md",
    "email": "support_policy.md",
    
    # Vietnamese keywords
    "hoàn tiền": "return_policy.md",
    "địa chỉ": "address_change_policy.md",
    "giao hàng": "shipping_policy.md",
    "hủy": "cancellation_policy.md",
    "thanh toán": "payment_policy.md",
    "bảo hành": "warranty_policy.md",
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
        
        # Initialize embeddings model - supports llama.cpp server
        self.embeddings_model = self._get_embeddings_model()
        
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
    
    def _get_embeddings_model(self):
        """Get embeddings model - supports llama.cpp server or OpenAI-compatible APIs.
        
        Configuration options:
        1. EMBEDDING_API_BASE + EMBEDDING_API_KEY: Use llama.cpp server or other OpenAI-compatible API
        2. DEEPSEEK_API_KEY: Use DeepSeek API with embeddings
        3. OPENAI_API_KEY: Use OpenAI embeddings
        
        Example llama.cpp server setup:
            ./llama-server -m embeddings.gguf --port 8080 --embeddings
            EMBEDDING_API_BASE=http://localhost:8080/v1
        """
        from app.services.embeddings import LlamaCppEmbeddings
        
        # Priority 1: Custom embedding API (llama.cpp server or other OpenAI-compatible)
        if self.settings.EMBEDDING_API_BASE:
            return LlamaCppEmbeddings(
                base_url=self.settings.EMBEDDING_API_BASE,
                model=self.settings.EMBEDDING_MODEL,
                api_key=self.settings.EMBEDDING_API_KEY or "dummy-key",
            )
        
        # Priority 2: DeepSeek API
        if self.settings.DEEPSEEK_API_KEY:
            return OpenAIEmbeddings(
                model=self.settings.EMBEDDING_MODEL,
                api_key=self.settings.DEEPSEEK_API_KEY,
            )
        
        # Priority 3: OpenAI API
        if self.settings.OPENAI_API_KEY:
            return OpenAIEmbeddings(
                model=self.settings.EMBEDDING_MODEL,
                api_key=self.settings.OPENAI_API_KEY,
            )
        
        # No embeddings available - will use keyword fallback
        return None
    
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
    
    def _split_into_chunks(self, text: str, chunk_size: int = 400, overlap: int = 100) -> list[str]:
        """Split text into smaller chunks with overlap for better retrieval.
        
        Uses a sliding window approach with overlap to ensure context continuity.
        Also extracts section headers for better context.
        """
        # First, extract section headers as separate chunks
        sections = []
        lines = text.split("\n")
        current_section = ""
        section_title = ""
        
        for line in lines:
            # Detect markdown headers
            if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                # Save previous section if exists
                if current_section.strip():
                    sections.append({
                        "title": section_title,
                        "content": current_section.strip(),
                    })
                section_title = line.replace("#", "").strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"
        
        # Add final section
        if current_section.strip():
            sections.append({
                "title": section_title,
                "content": current_section.strip(),
            })
        
        # Now create overlapping chunks from sections
        chunks = []
        all_text = "\n".join(s["content"] for s in sections)
        
        # Sliding window with overlap
        start = 0
        while start < len(all_text):
            end = min(start + chunk_size, len(all_text))
            chunk = all_text[start:end]
            
            # Try to find a good break point (newline)
            if end < len(all_text):
                last_newline = chunk.rfind("\n")
                if last_newline > chunk_size - overlap:
                    chunk = chunk[:last_newline]
                    end = start + last_newline
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            # Move start with overlap
            start = end - overlap if end < len(all_text) else end
        
        # Also add section headers as separate small chunks for better retrieval
        for section in sections:
            if section["title"]:
                title_chunk = f"{section['title']}\n{section['content'][:200]}"
                if title_chunk.strip() and title_chunk not in chunks:
                    chunks.insert(0, title_chunk)
        
        return chunks if chunks else [text[:chunk_size]]
    
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
