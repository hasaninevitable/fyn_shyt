import fitz  # PyMuPDF
import os
import json
from app.services.ocr import ocr_pdf_pages
import nltk
import nltk.data
import re

# Explicitly load the English Punkt tokenizer
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

HEADING_MAX_LENGTH = 8  # max number of words to consider as heading
HEADING_ALL_CAPS_RATIO = 0.7  # ratio of uppercase letters to total to guess heading
HEADING_SHORT_LINE_MAX_LENGTH = 60  # max char length of heading line to consider

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

def extract_text_coords(pdf_path, output_json_path):
    doc = fitz.open(pdf_path)
    data = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1, text, *_ = b
            text = text.strip()
            if not text:
                continue

            lines = text.split('\n')
            lines = merge_heading_lines(lines)
            lines = merge_lines_by_punctuation(lines)
            processed_text = '\n'.join(lines)

            sentences = tokenizer.tokenize(processed_text)
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    data.append({
                        "page": page_num + 1,
                        "text": sent,
                        "bbox": [x0, y0, x1, y1]
                    })

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return output_json_path

def extract_text_and_ocr(pdf_path, output_json_path, text_threshold=10):
    doc = fitz.open(pdf_path)
    data = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1, text, *_ = b
            text = text.strip()
            if not text:
                continue

            lines = text.split('\n')
            lines = merge_heading_lines(lines)
            lines = merge_lines_by_punctuation(lines)
            processed_text = '\n'.join(lines)

            sentences = tokenizer.tokenize(processed_text)
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    data.append({
                        "page": page_num + 1,
                        "text": sent,
                        "bbox": [x0, y0, x1, y1]
                    })

    if len(data) < text_threshold:
        ocr_data = ocr_pdf_pages(pdf_path)
        processed_ocr_data = []
        for block in ocr_data:
            text = block['text']
            lines = text.split('\n')
            lines = merge_heading_lines(lines)
            lines = merge_lines_by_punctuation(lines)
            processed_text = '\n'.join(lines)
            sentences = tokenizer.tokenize(processed_text)
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    processed_ocr_data.append({
                        "page": block['page'],
                        "text": sent,
                        "bbox": block['bbox']
                    })
        data.extend(processed_ocr_data)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"📝 Extracted {len(data)} text blocks")
    if data:
        print(f"🗒️ Sample text: {data[0]['text'][:100]}")
    else:
        print("⚠️ No extracted text found!")

    return output_json_path
