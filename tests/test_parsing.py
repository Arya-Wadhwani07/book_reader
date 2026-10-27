import io
import zipfile

import pytest
from pypdf import PdfWriter

from src.config import Settings
from src.parsing import chunk_book, extract_book


class CharacterTokenizer:
    def encode(self, text, **kwargs):
        return list(text)

    def decode(self, tokens):
        return "".join(tokens)


@pytest.fixture
def settings():
    return Settings(_env_file=None)


def parse(content, settings, filename="book.txt"):
    return extract_book(filename, content, settings, CharacterTokenizer())


def test_chapters_and_chunk_overlap_preserve_all_text(settings):
    original = b"CHAPTER I\nA beginning.\nCHAPTER II\nAn ending."
    book = parse(original, settings)
    assert len(book["sections"]) == 2
    chunks = chunk_book("book", book, CharacterTokenizer(), size=10, overlap=2)
    for section in book["sections"]:
        selected = [c for c in chunks if c["chapter"] == section["number"]]
        reconstructed = selected[0]["text"] + "".join(c["text"][2:] for c in selected[1:])
        assert reconstructed == section["text"]
    assert len({chunk["id"] for chunk in chunks}) == len(chunks)


@pytest.mark.parametrize(
    "content,filename,reason",
    [
        (b"", "book.txt", "empty"),
        (b"abc", "book.exe", "only"),
        (b"\xff", "book.txt", "UTF-8"),
        (b"a\x00b", "book.txt", "binary"),
        (b" ", "book.txt", "No readable"),
        (b"not zip", "book.epub", "cannot be read"),
        (b"not pdf", "book.pdf", "cannot be read"),
    ],
)
def test_bad_inputs_are_rejected(settings, content, filename, reason):
    with pytest.raises(ValueError, match=reason):
        parse(content, settings, filename)


def test_exact_byte_word_and_token_boundaries(settings):
    settings.max_upload_bytes = 5
    settings.max_tokens = 5
    settings.max_words = 3
    assert parse(b"a b c", settings)["words"] == 3
    with pytest.raises(ValueError, match="25 MB"):
        parse(b"a b cd", settings)
    settings.max_upload_bytes = 100
    with pytest.raises(ValueError, match="125,000 words"):
        parse(b"a b c d", settings)
    with pytest.raises(ValueError, match="250,000 tokens"):
        parse(b"abcdef", settings)


def test_pdf_page_cap_precedes_extraction(settings):
    output = io.BytesIO()
    writer = PdfWriter()
    for _ in range(501):
        writer.add_blank_page(width=72, height=72)
    writer.write(output)
    with pytest.raises(ValueError, match="500 physical pages"):
        parse(output.getvalue(), settings, "book.pdf")


def test_encrypted_pdf_rejected(settings):
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt("password")
    writer.write(output)
    with pytest.raises(ValueError, match="Encrypted"):
        parse(output.getvalue(), settings, "book.pdf")


@pytest.mark.parametrize("name", ["../escape.txt", "/outside.txt", "a\\b.txt"])
def test_epub_path_traversal_rejected(settings, name):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(name, "malicious")
    with pytest.raises(ValueError, match="unsafe"):
        parse(output.getvalue(), settings, "book.epub")


def test_epub_decompression_bomb_rejected(settings):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("huge.txt", b"a" * 100_000_001)
    with pytest.raises(ValueError, match="expanded"):
        parse(output.getvalue(), settings, "book.epub")


@pytest.mark.parametrize("pages", [300, 400, 500])
def test_representative_pdf_page_counts_with_extractable_text(settings, pages):
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    output = io.BytesIO()
    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    for number in range(pages):
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
        )
        content = DecodedStreamObject()
        content.set_data(
            f"BT /F1 12 Tf 50 700 Td (Page {number + 1}: the story continues.) Tj ET".encode()
        )
        page[NameObject("/Contents")] = writer._add_object(content)
    writer.write(output)
    result = parse(output.getvalue(), settings, "long_book.pdf")
    assert len(result["sections"]) == pages
    assert f"Page {pages}:" in result["sections"][-1]["text"]


def test_epub_reads_spine_order_and_removes_script(settings):
    from ebooklib import epub

    book = epub.EpubBook()
    book.set_identifier("offline-fixture")
    book.set_title("My test book")
    book.set_language("en")
    book.add_author("Test author")
    chapters = []
    for number in (1, 2):
        chapter = epub.EpubHtml(title=f"Chapter {number}", file_name=f"chapter_{number}.xhtml")
        chapter.content = f"<h1>Chapter {number}</h1><p>Text {number}</p><script>bad()</script>"
        book.add_item(chapter)
        chapters.append(chapter)
    book.toc = tuple(chapters)
    book.spine = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    output = io.BytesIO()
    epub.write_epub(output, book)
    result = parse(output.getvalue(), settings, "book.epub")
    assert result["title"] == "My test book"
    assert result["author"] == "Test author"
    assert [section["title"] for section in result["sections"]] == ["Chapter 1", "Chapter 2"]
    assert all("bad()" not in section["text"] for section in result["sections"])


@pytest.mark.parametrize("length", [1, 7, 799, 800, 801, 1480, 10000])
@pytest.mark.parametrize("overlap", [0, 1, 120, 799])
def test_chunk_boundary_reconstruction(settings, length, overlap):
    text = "abcdefg" * (length // 7) + "x" * (length % 7)
    extracted = parse(text.encode(), settings)
    chunks = chunk_book("book", extracted, CharacterTokenizer(), size=800, overlap=overlap)
    reconstructed = chunks[0]["text"] + "".join(c["text"][overlap:] for c in chunks[1:])
    assert reconstructed == text
    assert all(0 < len(chunk["text"]) <= 800 for chunk in chunks)


def test_contents_list_does_not_become_duplicate_chapters(settings):
    text = (
        "Title\nContents\nCHAPTER I. Beginning\nCHAPTER II. Ending\n\nCHAPTER I.\n"
        + "The narrative begins. " * 30
        + "\nCHAPTER II.\n"
        + "The narrative ends. " * 30
    )
    book = parse(text.encode(), settings)
    assert [section["title"] for section in book["sections"]] == ["CHAPTER I.", "CHAPTER II."]
    assert [section["number"] for section in book["sections"]] == [1, 2]
