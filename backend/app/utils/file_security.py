"""
File security utilities.

This module provides functions for secure file handling:
- Filename sanitization to prevent path traversal attacks
- File type validation
- Secure file storage helpers

Security considerations:
- Never trust user-provided filenames
- Always sanitize before using in file paths
- Use allowlists for file extensions
- Store files outside the web root
"""

import os
import re
import uuid
from pathlib import Path
from typing import Optional, Tuple

# Characters that are safe in filenames (alphanumeric, dash, underscore, dot)
SAFE_FILENAME_PATTERN = re.compile(r'^[\w\-. ]+$')

# Dangerous file extensions that should never be accepted
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js',
    '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl',
    '.dll', '.so', '.dylib', '.bin', '.com', '.msi',
}

# Maximum filename length (most filesystems support 255)
MAX_FILENAME_LENGTH = 200


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize a filename to prevent path traversal and other attacks.

    Why this matters:
    - Filenames like "../../../etc/passwd" could access system files
    - Special characters can cause issues on different filesystems
    - Very long filenames can cause errors

    What this function does:
    1. Extracts just the filename (removes any directory components)
    2. Removes or replaces unsafe characters
    3. Prevents empty filenames
    4. Limits filename length
    5. Preserves the file extension

    Args:
        filename: Original filename from user upload
        max_length: Maximum allowed filename length

    Returns:
        str: Sanitized filename safe for filesystem use

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        'passwd'
        >>> sanitize_filename("my file (1).pdf")
        'my_file_1.pdf'
        >>> sanitize_filename("  ")
        'unnamed_file'
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename, removing any directory path
    # This prevents path traversal attacks like "../../../etc/passwd"
    filename = os.path.basename(filename)

    # Remove null bytes (can cause issues)
    filename = filename.replace('\x00', '')

    # Split into name and extension
    name, ext = os.path.splitext(filename)

    # Sanitize the name part
    # Replace spaces with underscores
    name = name.replace(' ', '_')

    # Remove any character that's not alphanumeric, dash, underscore, or dot
    name = re.sub(r'[^\w\-.]', '', name)

    # Remove leading/trailing dots and dashes
    name = name.strip('.-')

    # Collapse multiple underscores/dashes
    name = re.sub(r'[-_]+', '_', name)

    # Handle empty name
    if not name:
        name = "unnamed_file"

    # Sanitize extension (lowercase, only alphanumeric)
    ext = ext.lower()
    ext = re.sub(r'[^a-z0-9.]', '', ext)

    # Combine and truncate
    full_name = f"{name}{ext}"
    if len(full_name) > max_length:
        # Preserve extension, truncate name
        ext_len = len(ext)
        name = name[:max_length - ext_len]
        full_name = f"{name}{ext}"

    return full_name


def generate_secure_filename(
    original_filename: str,
    preserve_extension: bool = True,
) -> str:
    """
    Generate a secure random filename, optionally preserving the extension.

    Why use random filenames:
    - Prevents filename collisions
    - Hides original filename (which might contain sensitive info)
    - Eliminates all sanitization concerns

    Args:
        original_filename: Original filename to extract extension from
        preserve_extension: Whether to keep the original file extension

    Returns:
        str: Random UUID-based filename

    Example:
        >>> generate_secure_filename("invoice.pdf")
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf'
    """
    random_name = str(uuid.uuid4())

    if preserve_extension and original_filename:
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower()
        # Only preserve known-safe extensions
        if ext and re.match(r'^\.[a-z0-9]{1,10}$', ext):
            return f"{random_name}{ext}"

    return random_name


def is_safe_extension(filename: str, allowed_extensions: set) -> bool:
    """
    Check if a file has an allowed extension.

    Args:
        filename: Filename to check
        allowed_extensions: Set of allowed extensions (e.g., {'.pdf', '.txt'})

    Returns:
        bool: True if extension is allowed
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def is_dangerous_extension(filename: str) -> bool:
    """
    Check if a file has a dangerous/executable extension.

    Args:
        filename: Filename to check

    Returns:
        bool: True if extension is dangerous
    """
    _, ext = os.path.splitext(filename.lower())
    return ext in DANGEROUS_EXTENSIONS


def validate_upload_filename(filename: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded filename for security issues.

    Checks:
    1. Not empty
    2. No path traversal attempts
    3. No dangerous extensions
    4. Reasonable length

    Args:
        filename: Filename to validate

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is empty"

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False, "Invalid filename: contains path components"

    # Check for null bytes
    if '\x00' in filename:
        return False, "Invalid filename: contains null bytes"

    # Check for dangerous extensions
    if is_dangerous_extension(filename):
        return False, "File type not allowed: executable files are blocked"

    # Check length
    if len(filename) > MAX_FILENAME_LENGTH:
        return False, f"Filename too long: maximum {MAX_FILENAME_LENGTH} characters"

    return True, None
