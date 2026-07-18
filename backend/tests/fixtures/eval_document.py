"""Synthetic multi-page study PDF used by the RAG eval set.

Four pages, each a distinct topic, so retrieval-accuracy checks can assert
the expected page was actually retrieved instead of just "some" chunk.
"""

from pathlib import Path

PAGES = [
    (
        "Cell Structure\n\n"
        "Mitochondria are organelles that generate most of a cell's chemical energy "
        "through cellular respiration, producing ATP from glucose and oxygen. "
        "They are often called the powerhouse of the cell because of this role."
    ),
    (
        "Photosynthesis\n\n"
        "Photosynthesis takes place inside chloroplasts, which contain the pigment "
        "chlorophyll. Chloroplasts capture sunlight and convert it into chemical "
        "energy stored in glucose, releasing oxygen as a byproduct."
    ),
    (
        "Genetics and Protein Synthesis\n\n"
        "The nucleus stores a cell's genetic information as DNA, organized into "
        "chromosomes. Ribosomes read messenger RNA copied from DNA and assemble "
        "amino acids into proteins, a process called translation."
    ),
    (
        "Ecosystems\n\n"
        "In an ecosystem, producers such as plants capture energy from sunlight, "
        "consumers obtain energy by eating producers or other consumers, and "
        "decomposers break down dead organic matter and recycle nutrients back "
        "into the soil."
    ),
]


def write_eval_pdf(path: Path) -> Path:
    import fitz

    document = fitz.open()
    for page_text in PAGES:
        page = document.new_page()
        page.insert_textbox(fitz.Rect(72, 72, 523, 770), page_text, fontsize=12)
    document.save(str(path))
    document.close()
    return path
