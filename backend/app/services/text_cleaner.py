import re


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_repeated_page_artifacts(pages: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    """Remove simple repeated headers and footers while preserving page numbers."""
    line_counts: dict[str, int] = {}
    page_count = len(pages)
    for page in pages:
        lines = _significant_lines(str(page.get("text", "")))
        for line in lines[:2] + lines[-2:]:
            line_counts[line] = line_counts.get(line, 0) + 1

    repeated = {
        line
        for line, count in line_counts.items()
        if page_count >= 3 and count >= max(3, int(page_count * 0.6))
    }
    if not repeated:
        return pages

    cleaned_pages: list[dict[str, str | int]] = []
    for page in pages:
        lines = str(page.get("text", "")).splitlines()
        kept = [line for line in lines if line.strip() not in repeated]
        cleaned_pages.append({**page, "text": clean_text("\n".join(kept))})
    return cleaned_pages


def _significant_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if 3 <= len(line.strip()) <= 120 and any(char.isalpha() for char in line)
    ]
