from pathlib import Path

from app.services.text_cleaner import clean_text


def extract_text(path: Path, content_type: str | None) -> list[dict[str, str | int]]:
    suffix = path.suffix.lower()
    if suffix == ".txt" or content_type == "text/plain":
        return [{"page_number": 1, "text": clean_text(path.read_text(encoding="utf-8", errors="ignore"))}]

    if suffix == ".pdf" or content_type == "application/pdf":
        try:
            import fitz
        except ImportError as exc:
            raise ValueError("PDF parsing dependency is not installed.") from exc

        pages: list[dict[str, str | int]] = []
        with fitz.open(path) as document:
            if document.needs_pass:
                raise ValueError("Password-protected PDFs are not supported.")
            for page_index, page in enumerate(document, start=1):
                page_text = clean_text(_extract_pdf_page_text(page))
                if page_text:
                    pages.append({"page_number": page_index, "text": page_text})
        return pages

    raise ValueError("Unsupported file type. Please upload a PDF or TXT file.")


def _extract_pdf_page_text(page) -> str:
    blocks = []
    for block in page.get_text("blocks"):
        if len(block) < 5:
            continue
        x0, y0, _, _, text = block[:5]
        cleaned = clean_text(str(text))
        if cleaned:
            blocks.append((float(y0), float(x0), cleaned))
    if not blocks:
        return str(page.get_text("text"))
    return "\n\n".join(text for _, _, text in sorted(blocks))
