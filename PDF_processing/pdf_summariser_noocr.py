import pdfplumber
from collections import defaultdict
from statistics import median

# =========================
# CONFIG
# =========================
Y_LINE_THRESHOLD = 3       # tolerance for grouping words into lines
PARA_GAP_THRESHOLD = 10    # vertical gap → new paragraph
HEADING_SIZE_DELTA = 1.0   # heading font size > body + delta


# =========================
# STAGE 1: WORD EXTRACTION
# =========================
def extract_words(pdf_path):
    all_pages_words = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
                extra_attrs=["size", "fontname"]
            )
            for w in words:
                w["page"] = page.page_number
            all_pages_words.extend(words)

    return all_pages_words


# =========================
# STAGE 2: WORDS → LINES
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
# STAGE 3: LINES → PARAGRAPHS
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
# STAGE 4: BODY FONT SIZE
# =========================
def estimate_body_font_size(words):
    sizes = [w["size"] for w in words]
    return median(sizes)


# =========================
# STAGE 5: HEADING DETECTION
# =========================
def is_heading(paragraph, body_font_size):
    sizes = [w["size"] for line in paragraph for w in line]
    avg_size = sum(sizes) / len(sizes)
    return avg_size > body_font_size + HEADING_SIZE_DELTA


# =========================
# STAGE 6: BUILD SECTIONS
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
# STAGE 7: LLM PLACEHOLDER
# =========================
def summarize_section(section):
    """
    Replace this with a real LLM API call.
    Keep this boundary clean.
    """
    content = " ".join(section["paragraphs"])
    return content[:300] + ("..." if len(content) > 300 else "")


# =========================
# MAIN PIPELINE
# =========================
def run_pipeline(pdf_path):
    words = extract_words(pdf_path)
    print(words)
    lines = group_words_into_lines(words)
    print(lines)
    paragraphs = lines_to_paragraphs(lines)
    print(paragraphs)
    body_font_size = estimate_body_font_size(words)
    print(body_font_size)
    sections = build_sections(paragraphs, body_font_size)
    print(sections)

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
    PDF_PATH = "/Users/hardik/Summariser/PDF_processing/pdfs/10610714.pdf"

    summaries = run_pipeline(PDF_PATH)

    for s in summaries:
        print("\n##", s["title"])
        print(s["summary"])
