"""PDF text extraction with OCR fallback."""

from pathlib import Path

MIN_TEXT_LENGTH = 50


def extract_text(pdf_path: Path) -> str:
    import pdfplumber

    pages_text: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""

            tables = page.extract_tables() or []
            table_parts: list[str] = []
            for table in tables:
                if not table:
                    continue
                rows: list[str] = []
                for i, row in enumerate(table):
                    cells = [str(c) if c is not None else "" for c in row]
                    rows.append("| " + " | ".join(cells) + " |")
                    if i == 0:
                        rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                if rows:
                    table_parts.append("\n".join(rows))

            content = text
            if table_parts:
                content += "\n\n" + "\n\n".join(table_parts)
            pages_text.append(f"--- Page {page_num} ---\n{content}")

    full_text = "\n\n".join(pages_text)

    if len(full_text.strip()) < MIN_TEXT_LENGTH:
        full_text = _ocr_fallback(pdf_path)

    return full_text


def _ocr_fallback(pdf_path: Path) -> str:
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(str(pdf_path))
    pages: list[str] = []
    for i, img in enumerate(images, start=1):
        text = pytesseract.image_to_string(img)
        pages.append(f"--- Page {i} (OCR) ---\n{text}")
    return "\n\n".join(pages)
