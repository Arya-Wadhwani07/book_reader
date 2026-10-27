import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup
from ebooklib import epub
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_book(filename, content, settings, tokenizer):
    if not content:
        raise ValueError("The book file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise ValueError("The file exceeds the 25 MB upload limit.")
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".epub", ".txt"}:
        raise ValueError("I accept only text-based PDF, EPUB, or TXT books.")
    title, author = Path(filename).stem, "Unknown author"
    if extension == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDFs are not supported.")
            if len(reader.pages) > settings.max_pdf_pages:
                raise ValueError("The PDF exceeds 500 physical pages.")
            sections = []
            for number, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                if not text.strip() and page.images:
                    raise ValueError("Image-only PDF pages require OCR and are not supported.")
                sections.append({"title": f"Page {number}", "page": number, "text": text})
            if reader.metadata:
                title = reader.metadata.title or title
                author = reader.metadata.author or author
        except PdfReadError as error:
            raise ValueError("The PDF cannot be read.") from error
    elif extension == ".epub":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                items = archive.infolist()
                if len(items) > 5000 or sum(i.file_size for i in items) > 100_000_000:
                    raise ValueError("The expanded EPUB exceeds the safe extraction limit.")
                if any(
                    PurePosixPath(i.filename).is_absolute()
                    or ".." in PurePosixPath(i.filename).parts
                    or "\\" in i.filename
                    for i in items
                ):
                    raise ValueError("The EPUB contains unsafe file paths.")
                if "META-INF/encryption.xml" in archive.namelist():
                    raise ValueError("Encrypted EPUB content is not supported.")
                for item in items:
                    if item.filename.lower().endswith((".xml", ".opf", ".ncx")):
                        document = archive.read(item)
                        if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", document, re.I):
                            raise ValueError("EPUB document types and entities are not supported.")
                        ET.fromstring(document)
            book = epub.read_epub(io.BytesIO(content))
            titles = book.get_metadata("DC", "title")
            authors = book.get_metadata("DC", "creator")
            title = titles[0][0] if titles else title
            author = authors[0][0] if authors else author
            sections = []
            for item_id, linear in book.spine:
                if linear == "no":
                    continue
                item = book.get_item_with_id(item_id)
                if item is None:
                    raise ValueError("The EPUB reading order references missing content.")
                soup = BeautifulSoup(item.get_content(), "html.parser")
                for unwanted in soup(["script", "style", "nav"]):
                    unwanted.decompose()
                heading = soup.find(["h1", "h2", "h3"])
                sections.append(
                    {
                        "title": heading.get_text(" ", strip=True)
                        if heading
                        else f"Section {len(sections) + 1}",
                        "page": None,
                        "text": soup.get_text(" ", strip=True),
                    }
                )
        except (zipfile.BadZipFile, KeyError, epub.EpubException, ET.ParseError) as error:
            raise ValueError("The EPUB cannot be read.") from error
    else:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError("TXT books must use UTF-8 encoding.") from error
        if "\x00" in text:
            raise ValueError("The TXT file contains binary content.")
        sections = split_text(text)

    sections = [section for section in sections if section["text"].strip()]
    text = "\n".join(section["text"] for section in sections)
    if not text.strip():
        raise ValueError("No readable text was found; scanned books require OCR.")
    words = len(text.split())
    if extension != ".pdf" and words > settings.max_words:
        raise ValueError("The book exceeds 125,000 words (approximately 500 pages).")
    tokens = tokenizer.encode(text, disallowed_special=())
    if len(tokens) > settings.max_tokens:
        raise ValueError("The extracted book exceeds 250,000 tokens.")
    for number, section in enumerate(sections, 1):
        section["number"] = number
    return {
        "title": str(title),
        "author": str(author),
        "sections": sections,
        "words": words,
        "tokens": len(tokens),
        "format": extension[1:],
    }


def split_text(text):
    headings = list(
        re.finditer(
            r"(?im)^\s*(?:chapter|part|book)\s+(?:\d+|[ivxlcdm]+|one|two|three|four|five)\b[^\n]*$",
            text,
        )
    )
    if not headings:
        return [{"title": "Full text", "page": None, "text": text}]
    # I exclude a repeated, heading-only contents list from narrative chapter numbering.
    contents_end = None
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        label = (
            re.match(r"\s*((?:chapter|part|book)\s+\w+)", heading.group(), re.I).group(1).lower()
        )
        later = [
            h
            for h in headings[index + 1 :]
            if re.match(r"\s*((?:chapter|part|book)\s+\w+)", h.group(), re.I).group(1).lower()
            == label
        ]
        if end - heading.end() < 100 and later:
            contents_end = (
                later[0].start() if contents_end is None else min(contents_end, later[0].start())
            )
        else:
            break
    if contents_end is not None and re.search(r"\bcontents\b", text[: headings[0].start()], re.I):
        return split_text(text[contents_end:])
    sections = []
    if text[: headings[0].start()].strip():
        sections.append(
            {"title": "Opening material", "page": None, "text": text[: headings[0].start()]}
        )
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        sections.append(
            {"title": heading.group().strip(), "page": None, "text": text[heading.start() : end]}
        )
    return sections


def chunk_book(book_id, extracted, tokenizer, size=800, overlap=120):
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than the chunk size.")
    chunks = []
    for section in extracted["sections"]:
        tokens = tokenizer.encode(section["text"], disallowed_special=())
        offset = 0
        while offset < len(tokens):
            end = min(offset + size, len(tokens))
            if hasattr(tokenizer, "decode_single_token_bytes"):
                # I extend a split UTF-8 character by at most its remaining token bytes.
                while end < len(tokens):
                    try:
                        tokenizer.decode(tokens[offset:end], errors="strict")
                        break
                    except UnicodeDecodeError:
                        end += 1
            part = tokens[offset:end]
            chunk_id = f"{book_id}-s{section['number']}-t{offset}"
            chunks.append(
                {
                    "id": chunk_id,
                    "book_id": book_id,
                    "source_id": book_id,
                    "chunk_id": chunk_id,
                    "chapter": section["number"],
                    "title": section["title"],
                    "page": section["page"],
                    "text": tokenizer.decode(part),
                }
            )
            if end >= len(tokens):
                break
            next_offset = max(offset + 1, end - overlap)
            if hasattr(tokenizer, "decode_single_token_bytes"):
                while next_offset < end:
                    first_byte = tokenizer.decode_single_token_bytes(tokens[next_offset])[0]
                    if first_byte & 0xC0 != 0x80:
                        break
                    next_offset += 1
            offset = next_offset
    return chunks
