import os
import io
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set Tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

ESG_KEYWORDS = [
    "carbon footprint", "greenhouse gas emissions", "SASB", "CDP", "GRI",
    "Sustainable Development Goals", "renewable energy", "water conservation",
    "waste reduction", "supply chain responsibility", "diversity and inclusion",
    "labor practices", "corporate governance", "stakeholder engagement"
]

def ocr_pdf(filepath):
    doc = fitz.open(filepath)
    page = doc[3]  # zero-based index for page 4
    print(f"Page 4 size: {page.rect}")  # prints rectangle with page dimensions (x0, y0, x1, y1)

    ocr_text = ""
    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        text = pytesseract.image_to_string(img)
        ocr_text += text + "\n"
    return ocr_text

def extract_esg_hits_with_coords(doc):
    hits = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("blocks")  # (x0,y0,x1,y1, text, ...)
        for b in blocks:
            x0, y0, x1, y1, block_text = b[0], b[1], b[2], b[3], b[4]
            # Split block text into sentences
            sentences = re.split(r'(?<=[.!?])\s+', block_text)
            for sentence in sentences:
                sentence_strip = sentence.strip()
                for kw in ESG_KEYWORDS:
                    if kw.lower() in sentence_strip.lower():
                        # Find rectangles for the exact sentence in this page
                        sentence_rects = page.search_for(sentence_strip)
                        for rect in sentence_rects:
                            hits.append({
                                "label": kw,
                                "page": page_num + 1,
                                "snippet": sentence_strip,
                                "rect": rect  # (x0, y0, x1, y1)
                            })
                        break  # Once matched on one keyword, stop checking others for this sentence
    return hits


def build_link(filename, page, rect):
    rect_str = ",".join(str(int(x)) for x in rect)
    return url_for('view_pdf', filename=filename, page=page, rect=rect_str)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            doc = fitz.open(filepath)

            # Add these lines to print page size for page 4 (index 3)
            if len(doc) > 3:
                page = doc[3]
                print(f"Page 4 size: {page.rect}")

            # Rest of your code ...

            text = ""
            for page in doc:
                text += page.get_text()

            if not text.strip():
                text = ocr_pdf(filepath)

            if not text.strip():
                return "No text found even after OCR. Please check document quality."

            # Call the hit extraction here
            hits = extract_esg_hits_with_coords(doc)

            classic_viewer_url = url_for('view_pdf', filename=file.filename)
            minimal_viewer_url = url_for('minimal_viewer', filename=file.filename)

            result_html = (
                f'<p><a href="{classic_viewer_url}" target="_blank">View full PDF report (Classic Viewer)</a></p>'
                f'<p><a href="{minimal_viewer_url}" target="_blank">View PDF (Minimal Viewer)</a></p>'
            )
            if hits:
                result_html += "<h2>ESG Initiatives Found:</h2><ul>"
                for hit in hits:
                    open_link = build_link(file.filename, hit['page'], hit['rect'])
                    snippet_short = hit['snippet'][:300]
                    result_html += f'<li><b>{hit["label"]}</b>: {snippet_short}... <a href="{open_link}" target="_blank">Open</a></li>'
                result_html += "</ul>"
            else:
                result_html += "No ESG-related information found in the document."
            return result_html
        else:
            return "Please upload a valid PDF file."

    return '''
        <h1>Upload ESG Report PDF</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required/>
            <input type="submit" value="Upload"/>
        </form>
    '''

@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    page = request.args.get('page', default=1, type=int)
    rect = request.args.get('rect', default=None)

    viewer_url = url_for('static', filename='pdfjs/viewer.html')
    pdf_url = url_for('uploaded_file', filename=filename)

    url = f"{viewer_url}?file={pdf_url}#page={page}"
    if rect:
        url += f"&rect={rect}"

    return redirect(url)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/minimal_viewer/<filename>')
def minimal_viewer(filename):
    pdfjs_url = url_for('static', filename='pdfjs/pdf.js')
    worker_url = url_for('static', filename='pdfjs/pdf.worker.js')
    pdf_url = url_for('uploaded_file', filename=filename)

    viewer_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Minimal PDF.js Viewer</title>
      <script src="{pdfjs_url}"></script>
      <script>
        pdfjsLib.GlobalWorkerOptions.workerSrc = "{worker_url}";
        const url = "{pdf_url}";
        const loadingTask = pdfjsLib.getDocument(url);
        loadingTask.promise.then(pdf => {{
          pdf.getPage(1).then(page => {{
            const scale = 1.5;
            const viewport = page.getViewport({{ scale: scale }});
            const canvas = document.getElementById('pdf-canvas');
            const ctx = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            const renderContext = {{
              canvasContext: ctx,
              viewport: viewport
            }};
            page.render(renderContext);
          }});
        }});
      </script>
    </head>
    <body>
      <canvas id="pdf-canvas"></canvas>
    </body>
    </html>
    '''
    return render_template_string(viewer_html)

if __name__ == '__main__':
    app.run(debug=True)
