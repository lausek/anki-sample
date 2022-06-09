#!/usr/bin/env python3

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import logging
import sqlite3


@dataclass
class Note:
    id: int
    guid: str
    mid: int
    mod: int
    usn: int

    tags: str
    flds: str

    sfld: int
    csum: int
    flags: int

    data: str

    def answer(self) -> str:
        _, answer_without_question = self.flds.split("\x1f")
        return answer_without_question.strip()

    def question(self) -> str:
        return self.sfld

    def from_row(row: tuple) -> Optional["Note"]:
        try:
            return Note(*row)
        except Exception:
            logging.warning("couldn't parse sql row.")
            return None


def load_deck_from_path(path: str) -> List[Note]:
    db = load_db_from_anki_file(path)
    return load_deck_from_deck(db)


def load_db_from_anki_file(deck_path: str) -> sqlite3.Connection:
    from hashlib import md5
    import tempfile
    import zipfile

    deck_digest = md5(deck_path.encode("utf-8")).hexdigest()
    extracted_deck_name = f"anki-sample-{deck_digest}"
    extracted_deck_path = Path(tempfile.gettempdir()) / extracted_deck_name

    with zipfile.ZipFile(deck_path) as zf:
        zf.extract("collection.anki2", extracted_deck_path)

        return sqlite3.connect(extracted_deck_path / "collection.anki2")


def load_deck_from_deck(db: sqlite3.Connection) -> List[Note]:
    questions_raw = db.execute("select * from notes").fetchall()
    return [*filter(bool, map(Note.from_row, questions_raw))]


def rich_format_answer_md(answer: str) -> str:
    from markdownify import markdownify

    return markdownify(answer)


def sample_deck_for_every_note(deck: List[Note]):
    return sample_deck_for_n_notes(deck, len(deck))


def sample_deck_for_n_notes(deck: List[Note], request_n_samples: int):
    import random

    from rich.console import Console
    from rich.markdown import Markdown
    from rich.padding import Padding

    console = Console()
    possible_samples_n = min(request_n_samples, len(deck))

    logging.info(f"loaded {len(deck)} notes.")
    logging.info(f"sampling {possible_samples_n} notes from deck.")

    for note in random.sample(deck, k=possible_samples_n):
        question, answer = note.question(), note.answer()

        console.print(f"[bold]Question: {question}[/]")
        input("reveal? [ENTER]")

        formatted_answer_md = rich_format_answer_md(answer)
        md = Markdown(formatted_answer_md)

        console.print(Padding(md, (1, 2, 2, 2)))


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("DECK_PATH", type=str)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--sample-all", action="store_true", default=False)
    parser.add_argument("--verbose", action="store_true", default=False)

    args = parser.parse_args()

    deck = load_deck_from_path(args.DECK_PATH)

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    if args.sample_all:
        sample_deck_for_every_note(deck)
    else:
        sample_deck_for_n_notes(deck, args.samples)


if __name__ == "__main__":
    from rich.logging import RichHandler

    logging.basicConfig(handlers=[RichHandler()])

    main()
