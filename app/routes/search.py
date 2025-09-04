import os
import json
import numpy as np
from flask import Blueprint, render_template, current_app, request, session
from app.services.search import model  # import model instance from service

search_bp = Blueprint("search", __name__)

ESG_KEYWORDS = [
    "climate change", "carbon emissions", "greenhouse gases",
    "diversity", "equity", "inclusion",
    "corporate governance", "transparency",
    # Add full ESG keyword list as needed
]

def contains_esg_keyword(sentence):
    sent_lower = sentence.lower()
    return any(word in sent_lower for word in ESG_KEYWORDS)

@search_bp.route("/search", methods=["GET"])
def search():
    filename = request.args.get("filename") or session.get("uploaded_filename")
    if not filename:
        return render_template("results.html", query=None, results=None, error="Filename missing.", filename=None)

    processed_folder = current_app.config['PROCESSED_FOLDER']
    json_path = os.path.join(processed_folder, "report.json")
    embeddings_path = os.path.join(processed_folder, "report_embeddings.npy")

    if not (os.path.exists(json_path) and os.path.exists(embeddings_path)):
        return render_template("results.html", query=None, results=None, error="Processed data not found.", filename=filename)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    embeddings = np.load(embeddings_path)

    # --- ESG sentence extraction in page order ---
    esg_results = []
    esg_embeddings = []

    # Sort blocks by page (ascending) as they appear in the PDF
    data.sort(key=lambda b: b.get("page", 0))

    for block, emb in zip(data, embeddings):
        if contains_esg_keyword(block.get("text", "")):
            esg_results.append(block)
            esg_embeddings.append(emb)

    if not esg_results:
        return render_template("results.html", query=None, results=None, error="No ESG sentences available in PDF.", filename=filename)

    esg_concept_text = "environmental social governance sustainability"
    esg_embedding = model.encode([esg_concept_text])[0]

    similarities = np.array([
        np.dot(esg_embedding, emb) / (np.linalg.norm(esg_embedding) * np.linalg.norm(emb))
        for emb in esg_embeddings
    ])

    # Build results, preserving page order, highest ESG match at the top of each page
    results = []
    for block, score in zip(esg_results, similarities):
        bbox_val = block.get("bbox", [])
        bbox_str = ",".join(str(x) for x in bbox_val) if isinstance(bbox_val, list) and len(bbox_val) == 4 else ""
        results.append({
            "text": block.get("text", ""),
            "page": block.get("page", 0),
            "bbox": bbox_str,
            "score": float(score)
        })

    # Final sort: strictly by page ascending, then by score descending (within page)
    results.sort(key=lambda x: (x["page"], -x["score"]))

    return render_template("results.html", query="ESG Semantic Search", results=results, filename=filename, error=None)
