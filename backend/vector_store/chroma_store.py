import chromadb
from pathlib import Path
from typing import Optional
from config import settings

_store: Optional["ChromaStore"] = None


class ChromaStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.chroma_db_dir))
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )

    def index_company_data(self, force: bool = False) -> int:
        """Index all markdown files in company_data/. Returns number of chunks added."""
        data_dir = settings.company_data_dir
        if not data_dir.exists():
            return 0

        existing_ids = set(self.collection.get()["ids"])
        chunks_added = 0

        for md_file in sorted(data_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            file_chunks = self._chunk_text(content, source=md_file.name)

            new_chunks = []
            for chunk_id, chunk_text in file_chunks:
                if chunk_id not in existing_ids or force:
                    new_chunks.append((chunk_id, chunk_text, md_file.name))

            if new_chunks:
                self.collection.add(
                    ids=[c[0] for c in new_chunks],
                    documents=[c[1] for c in new_chunks],
                    metadatas=[{"source": c[2]} for c in new_chunks],
                )
                chunks_added += len(new_chunks)

        return chunks_added

    def search(self, query: str, top_k: int = None) -> list[dict]:
        """Search the collection and return results with relevance scores."""
        top_k = top_k or settings.retrieval_top_k
        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # ChromaDB cosine distance: 0=identical, 2=opposite. Convert to similarity.
            score = max(0.0, 1.0 - dist)
            output.append({
                "file": meta.get("source", "unknown"),
                "chunk": doc,
                "relevance_score": round(score, 4),
            })

        return output

    def _chunk_text(
        self, text: str, source: str, chunk_size: int = 500, overlap: int = 50
    ) -> list[tuple[str, str]]:
        """Split text into overlapping word-level chunks. Returns (id, text) pairs."""
        words = text.split()
        chunks = []
        i = 0
        idx = 0
        while i < len(words):
            chunk_words = words[i: i + chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{source}::chunk_{idx}"
            chunks.append((chunk_id, chunk_text))
            i += chunk_size - overlap
            idx += 1
        return chunks


def get_store() -> ChromaStore:
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store
