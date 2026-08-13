from typing import Any, Dict, List, Optional
import chromadb

from config.constants import CHROMA_DIR, CHROMA_HOST, CHROMA_MODE, CHROMA_PORT
from core.logger import handle_errors, logger, time_execution

CHROMA_CLIENT = None


def get_chroma_client():
    """
    Lazy-loads and caches ChromaDB client.
    Uses local PersistentClient by default, or HttpClient if CHROMA_MODE is set to 'remote'.
    """
    global CHROMA_CLIENT
    if CHROMA_CLIENT is None:
        if CHROMA_MODE == "remote" and CHROMA_HOST:
            try:
                import socket
                sock = socket.create_connection((CHROMA_HOST, CHROMA_PORT), timeout=1.0)
                sock.close()
                logger.info(
                    f"Attempting connection to ChromaDB container at {CHROMA_HOST}:{CHROMA_PORT}..."
                )
                client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                client.heartbeat()
                CHROMA_CLIENT = client
                logger.info(
                    f"Successfully connected to ChromaDB container at {CHROMA_HOST}:{CHROMA_PORT}"
                )
                return CHROMA_CLIENT
            except Exception as e:
                logger.warning(
                    f"Remote ChromaDB container unreachable ({e}). Falling back to local PersistentClient at {CHROMA_DIR}."
                )

        logger.info(f"Initializing persistent local ChromaDB client at {CHROMA_DIR}...")
        CHROMA_CLIENT = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return CHROMA_CLIENT


def get_or_create_collection(collection_name: str = "memories"):
    """
    Retrieves or creates a ChromaDB collection using cosine similarity metric.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


@handle_errors
@time_execution
def add_chunks_to_vector_db(
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]],
    collection_name: str = "memories",
) -> Dict[str, Any]:
    """
    Upserts vector embeddings, chunk texts, and metadata into ChromaDB.
    """
    if not chunks or not embeddings:
        return {"status": "success", "added_count": 0}

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})."
        )

    collection = get_or_create_collection(collection_name)

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        # Extract chunk ID (supports 'chunk_id' or 'id')
        chunk_id = str(chunk.get("chunk_id") or chunk.get("id") or "")

        # Extract document text (supports 'text' or 'content')
        text = str(chunk.get("text") or chunk.get("content") or "")

        # Extract metadata (supports nested 'metadata' dict or top-level keys)
        meta = chunk.get("metadata", {}) if isinstance(chunk.get("metadata"), dict) else {}
        memory_id = str(meta.get("memory_id") or chunk.get("memory_id", ""))
        chunk_index = meta.get("chunk_index") if "chunk_index" in meta else chunk.get("chunk_index", 0)
        category = str(meta.get("category") or chunk.get("category", "personal"))

        tags_raw = meta.get("tags") if "tags" in meta else chunk.get("tags", [])
        if isinstance(tags_raw, list):
            tags_str = ",".join(tags_raw)
        else:
            tags_str = str(tags_raw or "")

        ids.append(chunk_id)
        documents.append(text)
        metadatas.append({
            "memory_id": memory_id,
            "chunk_index": chunk_index,
            "category": category,
            "tags": tags_str,
        })

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info(
        f"Successfully added/updated {len(ids)} chunks in ChromaDB ('{collection_name}')."
    )
    return {"status": "success", "added_count": len(ids), "chunk_ids": ids}


@handle_errors
@time_execution
def query_vector_db(
    query_embedding: List[float],
    n_results: int = 10,
    category_filter: Optional[str] = None,
    collection_name: str = "memories",
) -> List[Dict[str, Any]]:
    """
    Performs vector similarity search in ChromaDB with optional metadata filtering.
    """
    if not query_embedding:
        return []

    collection = get_or_create_collection(collection_name)
    where_clause = {"category": category_filter} if category_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    matched_chunks = []
    if results and results.get("ids") and results["ids"][0]:
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            similarity = round(max(0.0, 1.0 - dist), 4)
            tags_str = meta.get("tags", "")
            tags_list = tags_str.split(",") if tags_str else []

            matched_chunks.append({
                "chunk_id": chunk_id,
                "text": doc,
                "memory_id": meta.get("memory_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "category": meta.get("category", ""),
                "tags": tags_list,
                "distance": round(dist, 4),
                "similarity_score": similarity,
            })

    return matched_chunks


@handle_errors
def delete_chunks_by_memory_id(
    memory_id: str,
    collection_name: str = "memories",
) -> Dict[str, Any]:
    """
    Deletes all vector chunks matching a specific memory_id from ChromaDB.
    """
    collection = get_or_create_collection(collection_name)
    collection.delete(where={"memory_id": memory_id})

    logger.info(f"Deleted vector chunks for memory_id '{memory_id}' from ChromaDB.")
    return {"status": "success", "deleted_memory_id": memory_id}


@handle_errors
def peek_vector_db(
    limit: int = 10,
    collection_name: str = "memories",
) -> Dict[str, Any]:
    """
    Returns total item count and peeks at stored chunks in ChromaDB.
    """
    collection = get_or_create_collection(collection_name)
    total_count = collection.count()
    data = collection.get(limit=limit, include=["documents", "metadatas"])

    chunks = []
    if data and data.get("ids"):
        for chunk_id, doc, meta in zip(
            data["ids"], data["documents"], data["metadatas"]
        ):
            meta_dict = meta if isinstance(meta, dict) else {}
            tags_str = meta_dict.get("tags", "")
            tags_list = tags_str.split(",") if tags_str else []

            chunks.append({
                "chunk_id": chunk_id,
                "text": doc,
                "memory_id": meta_dict.get("memory_id", ""),
                "chunk_index": meta_dict.get("chunk_index", 0),
                "category": meta_dict.get("category", ""),
                "tags": tags_list,
            })

    return {
        "status": "success",
        "collection_name": collection_name,
        "total_chunks_in_db": total_count,
        "returned_count": len(chunks),
        "chunks": chunks,
    }


@handle_errors
def get_all_chunks(collection_name: str = "memories") -> List[Dict[str, Any]]:
    """
    Retrieves all stored chunk IDs and metadata from ChromaDB.
    """
    collection = get_or_create_collection(collection_name)
    data = collection.get(include=["metadatas"])
    chunks = []
    if data and data.get("ids"):
        for chunk_id, meta in zip(data["ids"], data["metadatas"]):
            meta_dict = meta if isinstance(meta, dict) else {}
            chunks.append({
                "chunk_id": chunk_id,
                "memory_id": meta_dict.get("memory_id", ""),
                "category": meta_dict.get("category", ""),
                "chunk_index": meta_dict.get("chunk_index", 0),
            })
    return chunks


@handle_errors
def delete_chunks_by_ids(
    chunk_ids: List[str],
    collection_name: str = "memories",
) -> Dict[str, Any]:
    """
    Deletes vector chunks by a list of chunk IDs from ChromaDB.
    """
    if not chunk_ids:
        return {"status": "success", "deleted_count": 0}

    collection = get_or_create_collection(collection_name)
    collection.delete(ids=chunk_ids)
    logger.info(f"Deleted {len(chunk_ids)} chunk IDs from ChromaDB collection '{collection_name}'.")
    return {"status": "success", "deleted_count": len(chunk_ids), "chunk_ids": chunk_ids}

