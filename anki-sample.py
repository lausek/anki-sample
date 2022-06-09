#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional

import logging
import sqlite3
import zipfile


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


def load_questions(db) -> List[Note]:
    questions_raw = db.execute("select * from notes").fetchall()
    return [*filter(bool, map(Note.from_row, questions_raw))]


def rich_format_answer_md(answer: str) -> str:
    from markdownify import markdownify

    return markdownify(answer)


def load_db_from_deck(deck_path: str) -> sqlite3.Connection:
    with zipfile.ZipFile(deck_path) as zf:
        zf.extract("collection.anki2")

        return sqlite3.connect("collection.anki2")


def sample_deck_for_n_notes(deck_path: str, request_n_samples: int):
    import random

    from rich.console import Console
    from rich.markdown import Markdown
    from rich.padding import Padding

    console = Console()

    db = load_db_from_deck(deck_path)
    notes = load_questions(db)

    logging.info(f"loaded {len(notes)} notes.")

    possible_samples_n = min(request_n_samples, len(notes))

    for note in random.sample(notes, k=possible_samples_n):
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

    args = parser.parse_args()

    sample_deck_for_n_notes(args.DECK_PATH, args.samples)


if __name__ == "__main__":
    from rich.logging import RichHandler
    logging.basicConfig(handlers=[RichHandler()])

    main()
