"""Custom embeddings wrapper supporting llama.cpp server format."""

from __future__ import annotations

from typing import Any

import httpx
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel


class LlamaCppEmbeddings(BaseModel, Embeddings):
    """Embeddings wrapper for llama.cpp server.
    
    llama.cpp server returns embeddings in a different format than OpenAI:
    - OpenAI: {"data": [{"embedding": [...], "index": 0}, ...]}
    - llama.cpp: [{"embedding": [...], "index": 0}, ...]  (no "data" wrapper)
    
    This wrapper handles both formats.
    """
    
    base_url: str
    model: str = "local-model"
    api_key: str = "dummy-key"
    
    def _parse_embedding_response(self, response_data: Any) -> list[float]:
        """Parse embedding from response, handling both OpenAI and llama.cpp formats."""
        # llama.cpp format: list of dicts directly
        if isinstance(response_data, list):
            if len(response_data) > 0 and "embedding" in response_data[0]:
                return response_data[0]["embedding"]
        
        # OpenAI format: {"data": [{"embedding": [...]}]}
        if isinstance(response_data, dict):
            if "data" in response_data:
                data = response_data["data"]
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("embedding", [])
        
        raise ValueError(f"Unexpected embedding response format: {type(response_data)}")
    
    def _get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings for a batch of texts."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key and self.api_key != "dummy-key":
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "input": texts,
            "model": self.model,
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        
        # Handle batch response
        embeddings = []
        
        # llama.cpp format: list of dicts directly
        if isinstance(data, list):
            for item in data:
                embeddings.append(item.get("embedding", []))
        # OpenAI format: {"data": [...]}
        elif isinstance(data, dict) and "data" in data:
            for item in data["data"]:
                embeddings.append(item.get("embedding", []))
        else:
            raise ValueError(f"Unexpected batch embedding response format: {type(data)}")
        
        return embeddings
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        return self._get_embeddings_batch(texts)
    
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        embeddings = self._get_embeddings_batch([text])
        return embeddings[0] if embeddings else []
    
    @classmethod
    def from_settings(cls) -> LlamaCppEmbeddings | None:
        """Create instance from app settings if configured."""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        if not settings.EMBEDDING_API_BASE:
            return None
        
        return cls(
            base_url=settings.EMBEDDING_API_BASE,
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY or "dummy-key",
        )
