import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from collections import defaultdict
from statistics import median

# =========================
# CONFIG
# =========================
Y_LINE_THRESHOLD = 3
PARA_GAP_THRESHOLD = 10
HEADING_SIZE_DELTA = 1.0
OCR_DPI = 300


# =========================
# PAGE TYPE DETECTION
# =========================
def is_scanned_page(page):
    text = page.extract_text()
    return text is None or len(text.strip()) < 20


# =========================
# OCR PAGE → WORDS
# =========================
def ocr_page_to_words(pdf_path, page_number):
    images = convert_from_path(
        pdf_path,
        dpi=OCR_DPI,
        first_page=page_number,
        last_page=page_number
    )

    image = images[0]
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    words = []
    for i in range(len(data["text"])):
        if data["text"][i].strip() == "":
            continue

        words.append({
            "text": data["text"][i],
            "x0": data["left"][i],
            "x1": data["left"][i] + data["width"][i],
            "top": data["top"][i],
            "bottom": data["top"][i] + data["height"][i],
            "size": 10,          # OCR has no font size → fake but consistent
            "fontname": "OCR",
            "page": page_number
        })

    return words


# =========================
# EXTRACT WORDS (TEXT + OCR)
# =========================
def extract_words(pdf_path):
    all_words = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            if is_scanned_page(page):
                ocr_words = ocr_page_to_words(pdf_path, page.page_number)
                all_words.extend(ocr_words)
            else:
                words = page.extract_words(
                    use_text_flow=False,
                    keep_blank_chars=False,
                    extra_attrs=["size", "fontname"]
                )
                for w in words:
                    w["page"] = page.page_number
                all_words.extend(words)

    return all_words


# =========================
# WORDS → LINES
# =========================
def group_words_into_lines(words):
    lines_map = defaultdict(list)

    for w in words:
        key = round(w["top"] / Y_LINE_THRESHOLD) * Y_LINE_THRESHOLD
        lines_map[(w["page"], key)].append(w)

    lines = []
    for (_, _), line_words in sorted(lines_map.items()):
        line_words = sorted(line_words, key=lambda x: x["x0"])
        lines.append(line_words)

    return lines


# =========================
# LINES → PARAGRAPHS
# =========================
def lines_to_paragraphs(lines):
    paragraphs = []
    current_para = []
    prev_bottom = None
    prev_page = None

    for line in lines:
        top = min(w["top"] for w in line)
        bottom = max(w["bottom"] for w in line)
        page = line[0]["page"]

        new_para = False
        if prev_page is not None and page != prev_page:
            new_para = True
        elif prev_bottom is not None and top - prev_bottom > PARA_GAP_THRESHOLD:
            new_para = True

        if new_para and current_para:
            paragraphs.append(current_para)
            current_para = []

        current_para.append(line)
        prev_bottom = bottom
        prev_page = page

    if current_para:
        paragraphs.append(current_para)

    return paragraphs


def paragraph_to_text(paragraph):
    return " ".join(
        " ".join(w["text"] for w in line)
        for line in paragraph
    ).strip()


# =========================
# BODY FONT SIZE (OCR SAFE)
# =========================
def estimate_body_font_size(words):
    sizes = [w["size"] for w in words if w["fontname"] != "OCR"]
    return median(sizes) if sizes else 10


# =========================
# HEADING DETECTION
# =========================
def is_heading(paragraph, body_font_size):
    sizes = [w["size"] for line in paragraph for w in line]
    avg_size = sum(sizes) / len(sizes)
    return avg_size > body_font_size + HEADING_SIZE_DELTA


# =========================
# BUILD SECTIONS
# =========================
def build_sections(paragraphs, body_font_size):
    sections = []
    current_section = {
        "title": "Introduction",
        "paragraphs": []
    }

    for para in paragraphs:
        text = paragraph_to_text(para)
        if not text:
            continue

        if is_heading(para, body_font_size):
            sections.append(current_section)
            current_section = {
                "title": text,
                "paragraphs": []
            }
        else:
            current_section["paragraphs"].append(text)

    sections.append(current_section)
    return sections


# =========================
# LLM PLACEHOLDER
# =========================
def summarize_section(section):
    content = " ".join(section["paragraphs"])
    return content[:300] + ("..." if len(content) > 300 else "")


# =========================
# MAIN PIPELINE
# =========================
def run_pipeline(pdf_path):
    words = extract_words(pdf_path)
    lines = group_words_into_lines(words)
    paragraphs = lines_to_paragraphs(lines)
    body_font_size = estimate_body_font_size(words)
    sections = build_sections(paragraphs, body_font_size)

    summaries = []
    for section in sections:
        summaries.append({
            "title": section["title"],
            "summary": summarize_section(section)
        })

    return summaries


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_summariser_ocr.py <pdf_path> [output_file]")
        sys.exit(1)
    
    PDF_PATH = sys.argv[1]
    
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found: {PDF_PATH}")
        sys.exit(1)
    
    summaries = run_pipeline(PDF_PATH)
    
    output_lines = []
    for s in summaries:
        output_lines.append(f"\n## {s['title']}")
        output_lines.append(s["summary"])
    
    output_text = "\n".join(output_lines)
    
    # If output file is provided, save to file; otherwise print to stdout
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"Extracted text saved to: {output_file}")
    else:
        print(output_text)
