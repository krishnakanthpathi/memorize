import hashlib
from pathlib import Path

from core.logger import handle_errors

@handle_errors
def compute_string_hash(content: str) -> str:
    """
    Computes a SHA-256 hash for a given text string.
    Used for checking if Markdown memory content has changed.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

@handle_errors
def compute_file_hash(file_path: Path, chunk_size: int = 65536) -> str:
    """
    Computes a SHA-256 hash for a binary media file (image, audio, video, document).
    Reads in chunks to handle large files efficiently without overloading memory.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()
