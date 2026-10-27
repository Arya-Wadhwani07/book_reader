"""I verify real cloud ingestion, source ownership, and all three upload formats."""

import argparse
import io
import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
from ebooklib import epub
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.config import ROOT


def fixtures():
    text = (
        "Clara visited the village library every morning. She discovered a blue notebook "
        "behind the history shelf. The notebook described a garden that the villagers had "
        "forgotten. Clara invited her friend Martin to restore the garden. They planted "
        "apple trees and shared the fruit with their neighbours. Their friendship grew "
        "stronger as they worked together. The garden became a peaceful meeting place. "
    ) * 3
    suffix = uuid.uuid4().hex[:8]
    yield f"garden_{suffix}.txt", text.encode()
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 40 740 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = stream
    output = io.BytesIO()
    writer.write(output)
    yield f"garden_{suffix}.pdf", output.getvalue()
    book = epub.EpubBook()
    book.set_identifier(suffix)
    book.set_title("The Village Garden")
    book.set_language("en")
    chapter = epub.EpubHtml(title="The garden", file_name="garden.xhtml", lang="en")
    chapter.content = f"<h1>The garden</h1><p>{text}</p>"
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.toc, book.spine = (chapter,), [chapter]
    output = io.BytesIO()
    epub.write_epub(output, book)
    yield f"garden_{suffix}.epub", output.getvalue()


def verify(url):
    results = []
    with (
        httpx.Client(base_url=url, timeout=120) as owner,
        httpx.Client(base_url=url, timeout=60) as other,
    ):
        owner.get("/api/bootstrap").raise_for_status()
        other.get("/api/bootstrap").raise_for_status()
        for filename, content in fixtures():
            started = time.monotonic()
            response = owner.post("/api/books", content=content, headers={"X-Filename": filename})
            response.raise_for_status()
            book = response.json()
            while book["status"] not in {"ready", "failed"} and time.monotonic() - started < 600:
                time.sleep(3)
                book = owner.get(f"/api/books/{book['id']}").json()
            assert book["status"] == "ready", book.get("error", book["status"])
            assert other.get(f"/api/books/{book['id']}").status_code == 404
            assert book["id"] not in {b["id"] for b in other.get("/api/books").json()}
            source = f"/api/books/{book['id']}/sources/{book['id']}-s1-t0"
            assert owner.get(source).json()["text"].strip()
            assert other.get(source).status_code == 404
            assert (
                owner.post(
                    "/api/books", content=content, headers={"X-Filename": filename}
                ).status_code
                == 409
            )
            results.append(
                {
                    "format": filename.rsplit(".", 1)[1],
                    "seconds": time.monotonic() - started,
                    "status": "passed",
                    "book_id": book["id"],
                }
            )
            print("Upload passed:", filename, flush=True)

        def read_ready(_):
            response = owner.get("/api/books")
            return response.status_code == 200 and len(response.json()) >= 11

        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=12) as pool:
            assert all(pool.map(read_ready, range(120)))
        results.append(
            {
                "concurrent_read_requests": 120,
                "workers": 12,
                "seconds": time.monotonic() - started,
                "status": "passed",
            }
        )
    (ROOT / "reports/uploads.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    verify(parser.parse_args().url)
