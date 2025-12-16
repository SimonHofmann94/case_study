"""
PDF text extraction utilities.

This module provides functions for extracting text content from PDF files
for use in AI-powered document parsing.
"""

import io
import logging
from pathlib import Path
from typing import Union, Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(
    source: Union[str, Path, bytes, io.BytesIO],
    max_pages: Optional[int] = None,
) -> str:
    """
    Extract text content from a PDF file.

    Args:
        source: Either a file path (str/Path), bytes content, or BytesIO object
        max_pages: Maximum number of pages to extract (None for all)

    Returns:
        Extracted text content as a string

    Raises:
        ValueError: If the PDF cannot be read or is empty
        FileNotFoundError: If the file path doesn't exist
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError(
            "pypdf is required for PDF extraction. "
            "Install it with: pip install pypdf"
        )

    try:
        # Handle different input types
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"PDF file not found: {path}")
            reader = PdfReader(str(path))
        elif isinstance(source, bytes):
            reader = PdfReader(io.BytesIO(source))
        elif isinstance(source, io.BytesIO):
            reader = PdfReader(source)
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        # Extract text from pages
        pages = reader.pages
        if max_pages:
            pages = pages[:max_pages]

        text_parts = []
        for i, page in enumerate(pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            except Exception as e:
                logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                continue

        if not text_parts:
            raise ValueError("No text content could be extracted from the PDF")

        full_text = "\n\n".join(text_parts)
        logger.info(
            f"Extracted {len(full_text)} characters from {len(text_parts)} pages"
        )
        return full_text

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        logger.error(f"Failed to read PDF: {e}")
        raise ValueError(f"Failed to read PDF file: {e}")


def extract_text_from_file(
    file_path: Union[str, Path],
    max_pages: Optional[int] = None,
) -> str:
    """
    Extract text from a file, supporting PDF and plain text.

    Args:
        file_path: Path to the file
        max_pages: Maximum pages to extract (for PDFs)

    Returns:
        Extracted text content

    Raises:
        ValueError: If file type is not supported
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(path, max_pages=max_pages)
    elif suffix in (".txt", ".text"):
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported types: .pdf, .txt"
        )


def get_pdf_metadata(source: Union[str, Path, bytes, io.BytesIO]) -> dict:
    """
    Extract metadata from a PDF file.

    Args:
        source: PDF file path, bytes, or BytesIO

    Returns:
        Dictionary with PDF metadata
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required for PDF extraction")

    # Handle different input types
    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
    elif isinstance(source, bytes):
        reader = PdfReader(io.BytesIO(source))
    elif isinstance(source, io.BytesIO):
        source.seek(0)
        reader = PdfReader(source)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")

    metadata = reader.metadata or {}

    return {
        "page_count": len(reader.pages),
        "title": metadata.get("/Title", ""),
        "author": metadata.get("/Author", ""),
        "subject": metadata.get("/Subject", ""),
        "creator": metadata.get("/Creator", ""),
        "producer": metadata.get("/Producer", ""),
    }
