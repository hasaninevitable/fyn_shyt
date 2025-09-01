import os
from flask import Blueprint, request, render_template, current_app
from app.services.extractor import extract_text_coords
from app.services.extractor import extract_text_and_ocr
from app.services.embeddings import generate_embeddings_from_json

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith('.pdf'):
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(upload_path)

            # Extract text + bbox JSON
            json_filename = file.filename.replace('.pdf', '.json')
            json_path = os.path.join(current_app.config['PROCESSED_FOLDER'], json_filename)
            extract_text_coords(upload_path, json_path)
            # inside upload route after saving the file:
            json_path = os.path.join(current_app.config['PROCESSED_FOLDER'], json_filename)
            extract_text_and_ocr(upload_path, json_path)
            # Generate embeddings for extracted JSON
            embeddings_filename = file.filename.replace('.pdf', '_embeddings.npy')
            embeddings_path = os.path.join(current_app.config['PROCESSED_FOLDER'], embeddings_filename)
            generate_embeddings_from_json(json_path, embeddings_path)

            return render_template("index.html", message="Upload, extraction, and embeddings successful!")
        else:
            return render_template("index.html", message="Please upload a PDF file.")
    return render_template("index.html")
