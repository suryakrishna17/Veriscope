"""Upload validation: content sniffing (never trust the extension), limits, safe names."""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..core.errors import ApiError

ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}
Image.MAX_IMAGE_PIXELS = 60_000_000  # decompression-bomb guard


@dataclass(frozen=True)
class ValidatedFile:
    data: bytes
    mime_type: str
    safe_name: str
    sha256: str
    page_count: int


def sniff_mime(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    return None


def safe_filename(name: str, ext: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", name.rsplit(".", 1)[0]).strip("._") or "document"
    return f"{stem[:80]}{ext}"


def validate_upload(data: bytes, filename: str, max_bytes: int, max_pages: int) -> ValidatedFile:
    if not data:
        raise ApiError(422, "EMPTY_FILE", "The file is empty. Choose a PDF, PNG or JPG that has content.")
    if len(data) > max_bytes:
        raise ApiError(413, "FILE_TOO_LARGE", f"The file is larger than {max_bytes // (1024 * 1024)} MB. Upload a smaller file.")
    mime = sniff_mime(data)
    if mime is None:
        raise ApiError(415, "UNSUPPORTED_FILE", "Only PDF, PNG and JPG files are accepted. The file content did not match any of these.")

    pages = 1
    if mime == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ApiError(422, "DOC_ENCRYPTED", "The PDF is password-protected. Upload an unlocked copy.")
            pages = len(reader.pages)
        except ApiError:
            raise
        except (PdfReadError, ValueError, KeyError, OSError) as e:
            raise ApiError(422, "DOC_CORRUPT", "The PDF could not be read. It may be damaged; export it again and re-upload.") from e
        if pages == 0:
            raise ApiError(422, "DOC_EMPTY", "The PDF has no pages.")
        if pages > max_pages:
            raise ApiError(422, "TOO_MANY_PAGES", f"The PDF has {pages} pages. The limit is {max_pages}.")
    else:
        try:
            with Image.open(io.BytesIO(data)) as im:
                im.verify()
            with Image.open(io.BytesIO(data)) as im:
                im.load()
                if min(im.size) < 200:
                    raise ApiError(422, "IMAGE_TOO_SMALL", "The image is too small to read. Upload a scan of at least 200 pixels per side.")
        except ApiError:
            raise
        except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as e:
            raise ApiError(422, "DOC_CORRUPT", "The image could not be read. It may be damaged; scan it again and re-upload.") from e

    return ValidatedFile(
        data=data,
        mime_type=mime,
        safe_name=safe_filename(filename or "document", ALLOWED[mime]),
        sha256=hashlib.sha256(data).hexdigest(),
        page_count=pages,
    )
