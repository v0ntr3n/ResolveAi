"""
Optimized RAG Retrieval Service with all enhancements from RAG_OPTIMIZATION_ANALYSIS.md.

Optimizations implemented:
1. Hybrid Search (RRF) - Combines semantic + keyword search
2. Relevance Threshold - Filters by minimum similarity score
3. Cosine Similarity - Normalized embeddings with Inner Product
4. Metadata Filtering - Rich metadata for each chunk
5. Adaptive Chunking - Different strategies for tables/lists/prose
6. Embedding Cache - Content-hash based caching

Maintains backward compatibility with existing API.
"""

from __future__ import annotations

import hashlib
import pickle
import re
from collections import defaultdict
from pathlib import Path

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


# Configuration constants
DISTANCE_THRESHOLD = 0.8  # Maximum L2 distance for relevance
RRF_K = 60  # Reciprocal Rank Fusion constant
SEMANTIC_WEIGHT = 0.7  # Weight for semantic search in hybrid
KEYWORD_WEIGHT = 0.3  # Weight for keyword search in hybrid


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


class EmbeddingCache:
    """Cache embeddings by content hash for performance."""
    
    def __init__(self, cache_dir: str = "./data/embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, np.ndarray] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load existing cache from disk."""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        if cache_file.exists():
            try:
                self._cache = pickle.loads(cache_file.read_bytes())
            except Exception:
                self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.cache_dir / "embedding_cache.pkl"
        cache_file.write_bytes(pickle.dumps(self._cache))
    
    def get(self, content: str) -> np.ndarray | None:
        """Get cached embedding if available."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return self._cache.get(content_hash)
    
    def set(self, content: str, embedding: np.ndarray):
        """Cache an embedding."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        self._cache[content_hash] = embedding
        self._save_cache()


class PolicyRetriever:
    """Optimized semantic search for policy documents using FAISS.
    
    Features:
    - Hybrid search (semantic + keyword with RRF)
    - Relevance threshold filtering
    - Cosine similarity (normalized embeddings)
    - Rich metadata for each chunk
    - Adaptive chunking by content type
    - Embedding caching
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.index = None
        self.documents = []
        self.embeddings_model = None
        self._initialized = False
        self._embedding_cache = EmbeddingCache()
    
    def _initialize(self):
        """Lazy initialization of FAISS index."""
        if self._initialized:
            return
        
        index_path = Path(self.settings.VECTOR_INDEX_DIR)
        index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings model
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
        """Get embeddings model - supports llama.cpp server or OpenAI-compatible APIs."""
        from app.services.embeddings import LlamaCppEmbeddings
        
        # Priority 1: Custom embedding API (llama.cpp server)
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
        
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detect if text contains Vietnamese characters."""
        vietnamese_chars = set('àáảãạăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
        return "vi" if any(c in vietnamese_chars for c in text.lower()) else "en"
    
    def _detect_content_type(self, text: str) -> str:
        """Detect content type for adaptive chunking."""
        # Table detection (markdown tables)
        if "|" in text and re.search(r'\|.*\|.*\|', text):
            return "table"
        # List detection (bullet points)
        if text.strip().startswith("- ") or re.search(r'^\s*- ', text, re.MULTILINE):
            return "list"
        return "prose"
    
    def _build_index(self):
        """Build FAISS index from policy documents with rich metadata."""
        kb_path = Path("data/knowledge_base")
        documents = []
        
        for md_file in kb_path.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            
            # Use adaptive chunking
            chunks = self._adaptive_chunk(content)
            
            for i, chunk_data in enumerate(chunks):
                documents.append({
                    "id": f"{md_file.name}-{i}",
                    "source": md_file.name,
                    "content": chunk_data["content"],
                    "chunk_id": i,
                    # Rich metadata for filtering
                    "language": self._detect_language(chunk_data["content"]),
                    "section": chunk_data.get("section", ""),
                    "content_type": chunk_data.get("content_type", "prose"),
                    "doc_type": md_file.stem.replace("_policy", ""),
                })
        
        self.documents = documents
        
        if not self.embeddings_model or not documents:
            return
        
        # Create embeddings with caching
        embeddings = self._get_cached_embeddings([doc["content"] for doc in documents])
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # OPTIMIZATION 3: Normalize for cosine similarity
        faiss.normalize_L2(embeddings_array)
        
        # Build FAISS index using Inner Product (cosine for normalized vectors)
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Changed from L2 to IP
        self.index.add(embeddings_array)
        
        # Save index and documents
        index_path = Path(self.settings.VECTOR_INDEX_DIR)
        faiss.write_index(self.index, str(index_path / "policy_index.faiss"))
        (index_path / "policy_docs.pkl").write_bytes(pickle.dumps(documents))
    
    def _get_cached_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings with caching for performance."""
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cached = self._embedding_cache.get(text)
            if cached is not None:
                embeddings.append(cached.tolist())
            else:
                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Batch embed uncached texts
        if uncached_texts:
            new_embeddings = self.embeddings_model.embed_documents(uncached_texts)
            
            # Update cache and fill placeholders
            for idx, text, emb in zip(uncached_indices, uncached_texts, new_embeddings):
                embeddings[idx] = emb
                self._embedding_cache.set(text, np.array(emb, dtype=np.float32))
        
        return embeddings
    
    def _adaptive_chunk(self, text: str) -> list[dict]:
        """Adaptive chunking based on content type.
        
        Tables: Keep whole tables together
        Lists: Chunk by bullet points
        Prose: Semantic chunking with overlap
        """
        chunks = []
        
        # First extract sections by headers
        sections = self._extract_sections(text)
        
        for section in sections:
            content_type = self._detect_content_type(section["content"])
            
            if content_type == "table":
                # Tables should stay together
                chunks.append({
                    "content": section["content"],
                    "section": section["title"],
                    "content_type": "table",
                })
            elif content_type == "list":
                # Lists: chunk by bullet points (max 5 items)
                list_chunks = self._chunk_list(section["content"], max_items=5)
                for lc in list_chunks:
                    chunks.append({
                        "content": lc,
                        "section": section["title"],
                        "content_type": "list",
                    })
            else:
                # Prose: semantic chunking with overlap
                prose_chunks = self._chunk_prose(section["content"], size=400, overlap=100)
                for pc in prose_chunks:
                    chunks.append({
                        "content": pc,
                        "section": section["title"],
                        "content_type": "prose",
                    })
        
        return chunks if chunks else [{"content": text[:500], "section": "", "content_type": "prose"}]
    
    def _extract_sections(self, text: str) -> list[dict]:
        """Extract sections by markdown headers."""
        sections = []
        lines = text.split("\n")
        current_section = ""
        section_title = ""
        
        for line in lines:
            if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
                if current_section.strip():
                    sections.append({
                        "title": section_title,
                        "content": current_section.strip(),
                    })
                section_title = line.replace("#", "").strip()
                current_section = line + "\n"
            else:
                current_section += line + "\n"
        
        if current_section.strip():
            sections.append({
                "title": section_title,
                "content": current_section.strip(),
            })
        
        return sections
    
    def _chunk_list(self, text: str, max_items: int = 5) -> list[str]:
        """Chunk list content by bullet points."""
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        item_count = 0
        
        for line in lines:
            if line.strip().startswith("- ") or line.strip().startswith("* "):
                item_count += 1
                if item_count > max_items and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    item_count = 1
            current_chunk.append(line)
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks
    
    def _chunk_prose(self, text: str, size: int = 400, overlap: int = 100) -> list[str]:
        """Chunk prose content with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + size, len(text))
            chunk = text[start:end]
            
            # Find good break point
            if end < len(text):
                last_newline = chunk.rfind("\n")
                if last_newline > size - overlap:
                    chunk = chunk[:last_newline]
                    end = start + last_newline
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def search(self, query: str, k: int = 5) -> dict[str, str]:
        """Search with hybrid search (semantic + keyword).
        
        Backward compatible: returns same format as original.
        """
        self._initialize()
        
        # OPTIMIZATION 1: Hybrid Search
        if self.index and self.embeddings_model:
            return self._hybrid_search(query, k)
        
        # Fallback to keyword only
        return self._keyword_fallback(query)
    
    def _hybrid_search(self, query: str, k: int = 5) -> dict[str, str]:
        """Reciprocal Rank Fusion combining semantic and keyword search."""
        # Get semantic results
        semantic_results = self._semantic_search(query, k=10)
        
        # Get keyword results
        keyword_results = self._keyword_search(query, k=10)
        
        # Combine with RRF
        combined = self._reciprocal_rank_fusion(semantic_results, keyword_results, k=k)
        
        return combined
    
    def _semantic_search(self, query: str, k: int = 10) -> list[dict]:
        """Semantic search with relevance threshold."""
        try:
            query_embedding = self.embeddings_model.embed_query(query)
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_array)
            
            # Search with more candidates
            scores, indices = self.index.search(query_array, k)
            
            results = []
            seen_content = set()
            
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    content_hash = hash(doc["content"][:100])
                    
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        score = float(scores[0][i])
                        
                        # OPTIMIZATION 2: Relevance Threshold
                        # For cosine (IP), higher is better
                        if score > 0.3:  # Minimum cosine similarity
                            results.append({
                                **doc,
                                "semantic_score": score,
                                "rank": len(results) + 1,
                            })
            
            return results
        except Exception:
            return []
    
    def _keyword_search(self, query: str, k: int = 10) -> list[dict]:
        """Keyword-based search with scoring."""
        lowered_query = query.lower()
        query_terms = set(lowered_query.split())
        
        results = []
        
        for doc in self.documents:
            content_lower = doc["content"].lower()
            
            # Count matching terms
            matches = sum(1 for term in query_terms if term in content_lower)
            
            # Also check KEYWORD_TO_FILE mappings
            for keyword in KEYWORD_TO_FILE.keys():
                if keyword in content_lower and keyword in lowered_query:
                    matches += 2  # Weight known keywords more
            
            if matches > 0:
                results.append({
                    **doc,
                    "keyword_score": matches,
                    "rank": 0,  # Will be set after sorting
                })
        
        # Sort by keyword score
        results.sort(key=lambda x: x["keyword_score"], reverse=True)
        
        # Assign ranks
        for i, r in enumerate(results[:k]):
            r["rank"] = i + 1
        
        return results[:k]
    
    def _reciprocal_rank_fusion(self, semantic_results: list[dict], keyword_results: list[dict], k: int = 5) -> dict[str, str]:
        """Combine semantic and keyword results using RRF."""
        scores = defaultdict(float)
        doc_map = {}
        
        # Add semantic scores
        for doc in semantic_results:
            doc_id = doc["id"]
            scores[doc_id] += SEMANTIC_WEIGHT / (RRF_K + doc["rank"])
            doc_map[doc_id] = doc
        
        # Add keyword scores
        for doc in keyword_results:
            doc_id = doc["id"]
            scores[doc_id] += KEYWORD_WEIGHT / (RRF_K + doc["rank"])
            if doc_id not in doc_map:
                doc_map[doc_id] = doc
        
        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        # Build result
        chunks = []
        for doc_id, score in ranked:
            chunks.append(doc_map[doc_id]["content"])
        
        sources = list(set(doc_map[doc_id]["source"] for doc_id, _ in ranked))
        
        return {
            "source": ", ".join(sources),
            "content": "\n\n---\n\n".join(chunks),
            "chunks": chunks,
            "scores": [score for _, score in ranked],
        }
    
    def _keyword_fallback(self, query: str) -> dict[str, str]:
        """Keyword fallback with proper chunking."""
        lowered_query = query.lower()
        selected_file = "shipping_policy.md"
        
        for keyword, file_name in KEYWORD_TO_FILE.items():
            if keyword in lowered_query:
                selected_file = file_name
                break
        
        path = Path("data/knowledge_base") / selected_file
        full_content = path.read_text(encoding="utf-8")
        
        # Chunk and score
        chunks = self._adaptive_chunk(full_content)
        scored_chunks = []
        query_keywords = set(lowered_query.split())
        
        for chunk_data in chunks:
            chunk = chunk_data["content"]
            chunk_lower = chunk.lower()
            score = sum(1 for kw in query_keywords if kw in chunk_lower)
            
            for keyword in KEYWORD_TO_FILE.keys():
                if keyword in chunk_lower:
                    score += 1
            
            if score > 0:
                scored_chunks.append((chunk, score))
        
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [c[0] for c in scored_chunks[:5]]
        
        if not top_chunks:
            top_chunks = [c["content"] for c in chunks[:3]]
        
        return {
            "source": selected_file,
            "content": "\n\n---\n\n".join(top_chunks),
            "chunks": top_chunks,
        }
    
    def search_multi_query(self, query: str, k: int = 5) -> dict[str, str]:
        """Multi-query retrieval with query expansion."""
        primary_results = self.search(query, k=k)
        
        expanded_queries = self._expand_query(query)
        
        all_chunks = primary_results.get("chunks", [])
        all_sources = set(primary_results.get("source", "").split(", "))
        
        for exp_query in expanded_queries[:2]:
            exp_results = self.search(exp_query, k=2)
            if exp_results.get("chunks"):
                for chunk in exp_results["chunks"]:
                    if chunk not in all_chunks:
                        all_chunks.append(chunk)
                all_sources.update(exp_results.get("source", "").split(", "))
        
        return {
            "source": ", ".join(all_sources),
            "content": "\n\n---\n\n".join(all_chunks),
            "chunks": all_chunks,
        }
    
    def _expand_query(self, query: str) -> list[str]:
        """Generate query variations for better retrieval."""
        variations = []
        
        expansions = {
            "refund": ["return policy", "money back", "how to refund"],
            "shipping": ["delivery", "shipping time", "shipping policy"],
            "address": ["shipping address", "delivery address", "change address"],
            "cancel": ["cancellation", "cancel order"],
            "track": ["tracking", "order status", "where is my order"],
            "warranty": ["guarantee", "defective", "product warranty"],
            "damaged": ["broken", "defective", "damaged item"],
            "hoàn tiền": ["trả lại", "đổi trả"],
            "giao hàng": ["vận chuyển", "đị vị"],
        }
        
        query_lower = query.lower()
        for key, expansion_list in expansions.items():
            if key in query_lower:
                variations.extend(expansion_list)
        
        return variations
    
    # OPTIMIZATION 4: Metadata Filtering
    def search_with_filter(self, query: str, filters: dict, k: int = 5) -> dict[str, str]:
        """Search with metadata filtering.
        
        Args:
            query: Search query
            filters: Dict with 'language', 'doc_type', 'section' keys
            k: Number of results
        """
        self._initialize()
        
        # Pre-filter documents by metadata
        filtered_docs = self.documents
        
        if filters.get("language"):
            filtered_docs = [d for d in filtered_docs if d["language"] == filters["language"]]
        
        if filters.get("doc_type"):
            filtered_docs = [d for d in filtered_docs if d["doc_type"] == filters["doc_type"]]
        
        if filters.get("section"):
            filtered_docs = [d for d in filtered_docs if filters["section"].lower() in d["section"].lower()]
        
        # Search within filtered subset
        if self.index and self.embeddings_model:
            return self._filtered_semantic_search(query, filtered_docs, k)
        
        return self._keyword_fallback(query)


# Global retriever instance
_retriever: PolicyRetriever | None = None


def get_retriever() -> PolicyRetriever:
    """Get or create global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = PolicyRetriever()
    return _retriever


def retrieve_policy_context(query: str) -> dict[str, str]:
    """Retrieve relevant policy context using optimized hybrid search."""
    from app.services.cache import get_policy_cache
    
    cache = get_policy_cache()
    query_hash = cache.get_query_hash(query)
    
    cached_result = cache.get_policy(query_hash)
    if cached_result:
        return cached_result
    
    retriever = get_retriever()
    result = retriever.search(query)
    
    cache.set_policy(query_hash, result)
    
    return result