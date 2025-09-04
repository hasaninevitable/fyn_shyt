import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def semantic_search(query, embeddings, data, top_k=5):
    """
    query: str, user search query
    embeddings: numpy ndarray of shape (n_blocks, embedding_dim)
    data: list of dicts, JSON data with 'text', 'page', and 'bbox'
    top_k: int, number of results to return

    Returns top_k matches sorted by similarity score.
    """
    query_embedding = model.encode([query])[0]
    sims = np.array([cosine_similarity(query_embedding, emb) for emb in embeddings])

    # Get indices for top_k highest similarity scores
    top_indices = sims.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        results.append({
            "text": data[idx]["text"],
            "page": data[idx]["page"],
            "bbox": data[idx]["bbox"],
            "score": float(sims[idx])
        })

    return results
