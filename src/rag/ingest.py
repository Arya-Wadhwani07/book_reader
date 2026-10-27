import asyncio
import os

from src.config import Settings
from src.library import Library
from src.store import make_store


def main():
    settings = Settings()
    library = Library(settings, make_store(settings))
    asyncio.run(library.ingest(os.environ["BOOK_ID"]))


if __name__ == "__main__":
    main()
