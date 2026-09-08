
import chromadb

from app.config import CHROMA_DIR, COLLECTION_NAME


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(chunks, embeddings):
    collection = get_collection()

    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )

    return len(chunks)


def search(query_embedding, top_k=5):
    collection = get_collection()

    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []

    ids = result["ids"][0]
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    for chunk_id, text, meta, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        output.append({
            "chunk_id": chunk_id,
            "text": text,
            "score": max(0.0, 1.0 - float(distance)),
            **meta,
        })

    return output

