"""Upload validation: content sniffing (never trust the extension), limits, safe names."""
from __future__ import annotations

import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    PdfReader = None  # type: ignore[assignment]

    class PdfReadError(Exception):  # type: ignore[no-redef]
        pass

from ..core.errors import ApiError

ALLOWED = {"application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg"}
Image.MAX_IMAGE_PIXELS = 60_000_000  # decompression-bomb guard
MAX_PAGE_POINTS = 3400  # ~47 inches max
MIN_PAGE_POINTS = 36    # 0.5 inches min


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


def sanitize_filename(name: str, ext: str) -> str:
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
        if PdfReader is not None:
            try:
                reader = PdfReader(io.BytesIO(data))
                if reader.is_encrypted:
                    raise ApiError(422, "DOC_ENCRYPTED", "The PDF is password-protected. Upload an unlocked copy.")
                pages = len(reader.pages)
                for idx, page in enumerate(reader.pages):
                    try:
                        box = page.mediabox
                        width = float(abs(box.width))
                        height = float(abs(box.height))
                        if width > MAX_PAGE_POINTS or height > MAX_PAGE_POINTS:
                            raise ApiError(
                                422,
                                "PAGE_SIZE_UNSUPPORTED",
                                f"Page {idx + 1} dimensions ({width:.0f}x{height:.0f} pt) exceed the maximum supported page size ({MAX_PAGE_POINTS} pt).",
                            )
                        if width < MIN_PAGE_POINTS or height < MIN_PAGE_POINTS:
                            raise ApiError(
                                422,
                                "PAGE_SIZE_UNSUPPORTED",
                                f"Page {idx + 1} dimensions ({width:.0f}x{height:.0f} pt) are smaller than the minimum supported page size ({MIN_PAGE_POINTS} pt).",
                            )
                    except ApiError:
                        raise
                    except Exception:
                        pass
            except ApiError:
                raise
            except (PdfReadError, ValueError, KeyError, OSError) as e:
                raise ApiError(422, "DOC_CORRUPT", "The PDF could not be read. It may be damaged; export it again and re-upload.") from e
        else:
            pages = max(1, len(re.findall(rb"/Type\s*/Page\b", data)))
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
        except (UnidentifiedImageError, OSError, ValueError) as e:
            raise ApiError(422, "DOC_CORRUPT", "The image could not be read. Check the file and re-upload.") from e

    return ValidatedFile(
        data=data,
        mime_type=mime,
        safe_name=sanitize_filename(filename, ALLOWED[mime]),
        sha256=hashlib.sha256(data).hexdigest(),
        page_count=pages,
    )
