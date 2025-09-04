import os
from flask import Blueprint, request, redirect, url_for, current_app, render_template, session

from app.services.extractor import extract_text_coords, extract_text_and_ocr
from app.services.embeddings import generate_embeddings_from_json

upload_bp = Blueprint('upload', __name__)

@upload_bp.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith('.pdf'):
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(upload_path)

            # Store filename in session
            session['uploaded_filename'] = file.filename

            json_filename = file.filename.replace('.pdf', '.json')
            json_path = os.path.join(current_app.config['PROCESSED_FOLDER'], json_filename)

            extract_text_coords(upload_path, json_path)
            extract_text_and_ocr(upload_path, json_path)

            embeddings_filename = file.filename.replace('.pdf', '_embeddings.npy')
            embeddings_path = os.path.join(current_app.config['PROCESSED_FOLDER'], embeddings_filename)
            generate_embeddings_from_json(json_path, embeddings_path)

            # Pass filename as query parameter to search page
            return redirect(url_for('search.search', filename=file.filename))
        else:
            return render_template("index.html", message="Please upload a PDF file.")
    return render_template("index.html")
