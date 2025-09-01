import os
import json
import numpy as np
from flask import Blueprint, request, jsonify, current_app
from app.services.search import semantic_search

search_bp = Blueprint("search", __name__)

@search_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    processed_folder = current_app.config['PROCESSED_FOLDER']

    embedding_path = os.path.join(processed_folder, "report_embeddings.npy")
    json_path = os.path.join(processed_folder, "report.json")

    if not (os.path.exists(embedding_path) and os.path.exists(json_path)):
        return jsonify({"error": "Processed data not found"}), 404

    embeddings = np.load(embedding_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = semantic_search(query, embeddings, data, top_k=5)
    print(f"Query received: {query}")
    print(f"Embedding path: {embedding_path}")
    print(f"JSON path: {json_path}")
    print(f"Number of text blocks: {len(data)}")

    return jsonify({"query": query, "results": results})
