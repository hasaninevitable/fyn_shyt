import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Load SentenceTransformer once when module is imported
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embeddings_from_json(json_path, output_path):
    """
    Given a JSON file with text blocks, generate embeddings for each text block
    and save them as a numpy .npy file.

    JSON format assumed:
    [
      {"page": 1, "text": "Carbon emissions reduced by 15%", "bbox": [x0, y0, x1, y1]},
      ...
    ]

    output_path: e.g. processed/sample_embeddings.npy
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = [item['text'] for item in data]
    embeddings = model.encode(texts, show_progress_bar=True)

    np.save(output_path, embeddings)
    print(f"🔢 Generated embeddings for {len(embeddings)} text blocks")
    print(f"🔍 Embedding vector dimension: {len(embeddings[0]) if len(embeddings) > 0 else 'N/A'}")

    return output_path


def load_embeddings(embedding_path):
    """
    Load precomputed embeddings from a .npy file.
    """
    return np.load(embedding_path)
