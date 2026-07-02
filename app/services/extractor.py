import fitz  # PyMuPDF


def extract_text(file_path: str, file_type: str) -> str:
    """
    Extract raw text from a PDF or TXT file.

    Args:
        file_path: Absolute or relative path to the file on disk.
        file_type: Either 'pdf' or 'txt'.

    Returns:
        Extracted text as a single string.

    Raises:
        ValueError: If file_type is not 'pdf' or 'txt'.
    """
    if file_type == "pdf":
        return _extract_from_pdf(file_path)
    elif file_type == "txt":
        return _extract_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: '{file_type}'. Use 'pdf' or 'txt'.")


def _extract_from_pdf(file_path: str) -> str:
    """Read all pages of a PDF and concatenate their text."""
    doc = fitz.open(file_path)
    pages: list[str] = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages).strip()


def _extract_from_txt(file_path: str) -> str:
    """Read a plain-text file with UTF-8 encoding."""
    with open(file_path, encoding="utf-8") as f:
        return f.read().strip()
