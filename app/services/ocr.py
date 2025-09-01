import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import nltk
from nltk.tokenize import sent_tokenize
import re

nltk.download('punkt')

HEADING_MAX_LENGTH = 8
HEADING_ALL_CAPS_RATIO = 0.7
HEADING_SHORT_LINE_MAX_LENGTH = 60

def looks_like_heading(text):
    text = text.strip()
    if not text:
        return False
    if len(text) > HEADING_SHORT_LINE_MAX_LENGTH or len(text.split()) > HEADING_MAX_LENGTH:
        return False
    caps = sum(1 for c in text if c.isupper())
    ratio = caps / max(len(text.replace(" ", "")), 1)
    if ratio >= HEADING_ALL_CAPS_RATIO:
        return True
    if re.match(r'^([A-Z][a-z]+(\s|$)){1,8}$', text):
        return True
    return False

def insert_period_after_heading(text):
    text = text.strip()
    if text.endswith(('.', ':', '?', '!')):
        return text
    else:
        return text + '.'

def merge_heading_lines(lines):
    merged = []
    buffer = []
    for line in lines:
        if looks_like_heading(line):
            buffer.append(line.strip())
        else:
            if buffer:
                heading = " ".join(buffer)
                merged.append(insert_period_after_heading(heading))
                buffer = []
            merged.append(line)
    if buffer:
        heading = " ".join(buffer)
        merged.append(insert_period_after_heading(heading))
    return merged

def merge_lines_by_punctuation(lines):
    merged = []
    buffer = []

    for line in lines:
        stripped = line.strip()
        if not buffer:
            buffer.append(stripped)
        else:
            if buffer[-1].endswith(('.', '?', '!', ':')):
                merged.append(" ".join(buffer))
                buffer = [stripped]
            else:
                buffer.append(stripped)
    if buffer:
        merged.append(" ".join(buffer))
    return merged

def ocr_pdf_pages(pdf_path):
    """
    Perform OCR on each page of the PDF.
    Returns a list of dicts with keys: 'page', 'text', 'bbox'.
    bbox here is a full page bbox placeholder.
    Splits OCR output text into sentences with the full-page bbox assigned,
    applying heading separation logic including multi-line heading merging
    and line merging by punctuation.
    """
    doc = fitz.open(pdf_path)
    ocr_results = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)  # render image at 300 dpi
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        text = pytesseract.image_to_string(img).strip()
        if not text:
            continue

        lines = text.split('\n')
        lines = merge_heading_lines(lines)
        lines = merge_lines_by_punctuation(lines)
        processed_text = '\n'.join(lines)

        sentences = sent_tokenize(processed_text)
        for sent in sentences:
            sent = sent.strip()
            if sent:
                ocr_results.append({
                    "page": page_num + 1,
                    "text": sent,
                    "bbox": [0, 0, pix.width, pix.height]  # Full page bbox
                })

    return ocr_results
