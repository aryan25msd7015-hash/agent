from __future__ import annotations

from typing import Any

import chromadb


class MemoryStore:
    def __init__(self, path: str = "data/chroma") -> None:
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection("agent_memory")

    def add_fact(self, fact_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        self.collection.upsert(
            ids=[fact_id],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search(self, query: str, n_results: int = 3) -> list[str]:
        res = self.collection.query(query_texts=[query], n_results=n_results)
        docs = res.get("documents", [[]])
        return docs[0] if docs else []
