"""Utilities for parsing CSV files with details about sections."""

from __future__ import annotations

import csv
import logging
import sys
from argparse import ArgumentParser
from collections.abc import Iterable, Iterator
from io import TextIOBase
from pathlib import Path

from .names import SectionDetails

logger = logging.getLogger(__name__)


def write_sections_csv(writeable: TextIOBase, details: Iterable[SectionDetails]) -> int:
    """Write a CSV file with details of sections taken from each biopsy.

    Parameters
    ----------
    writeable:
        Anything with a `.write(str)` method,
        e.g. the result of `open("path/to/new.csv", "w")`,
        `sys.stdout`, or `io.StringIO`.
    details:
        SectionDetails to write.

    Returns
    -------
    int
        Number of rows written (including headers).

    Examples
    --------
    >>> from wtdtk.names import SectionModality
    >>>
    >>> section = SectionDetails(3, [SectionModality.HE], 5, "Glass")
    >>> with open("path/to/new.csv", "w") as f:
    ...     write_sections(f, [section])

    """
    w = csv.writer(writeable)
    w.writerow(SectionDetails.headers())
    count = 1
    for d in details:
        w.writerow(d.to_row())
        count += 1
    return count


def read_sections_csv(lines: Iterable[str]) -> Iterable[SectionDetails]:
    """Read a CSV file with details of sections taken from each biopsy.

    Parameters
    ----------
    lines:
        Lines of a csv,
        e.g. the result of `open("path/to/details.csv", newline="")`,
        or `details_csv_str.splitlines()`.
    fpath:
        If given, log messages are slightly more informative.

    Yields
    ------
    SectionDetails
        Details of each section described in the CSV.

    Examples
    --------
    >>> with open("path/to/details.csv", newline="") as f:
    ...     sections = list(read_sections_csv(f))
    """
    yield from SectionsCsvReader(lines)


class InvalidCsv(ValueError):
    pass


def fmt_expected_got(expected, got, prefix: str = "", separator="\n") -> str:
    expected_str = "expected"
    got_str = "got".ljust(len(expected_str))
    return f"{prefix}{expected_str}: {expected}{separator}{prefix}{got_str}: {got}"


class SectionsCsvReader:
    def __init__(self, lines: Iterable[str]) -> None:
        self.reader = csv.reader(lines)

    def consume_headers(self):
        line = next(self.reader, None)
        expected = SectionDetails.headers()
        if line != expected:
            raise InvalidCsv(
                f"Header mismatch: {fmt_expected_got(expected, line, '  ', ', ')}"
            )

    def consume_row(self) -> SectionDetails | None:
        row = next(self.reader, None)
        if row is None:
            return row
        return SectionDetails.from_row(row)

    def _iter_inner(self) -> Iterator[tuple[int, SectionDetails | Exception]]:
        try:
            self.consume_headers()
        except InvalidCsv as e:
            yield (0, e)

        idx = 0
        while True:
            idx += 1
            try:
                row = self.consume_row()
            except Exception as e:  # noqa: BLE001
                yield (idx, e)
                continue
            if row is None:
                return
            yield (idx, row)

    def __iter__(self) -> Iterator[SectionDetails]:
        for idx, res in self._iter_inner():
            if isinstance(res, Exception):
                if idx == 0:
                    logger.warning("%s", res)
                    continue
                else:
                    raise res
            yield res

    def iter_problems(self) -> Iterator[tuple[int, str]]:
        for idx, res in self._iter_inner():
            if isinstance(res, Exception):
                yield (idx, str(res))


def _validate_sections_csv(fpaths: list[Path]):
    errs = 0
    if len(fpaths) <= 1:
        logger.info("Nothing to do")
        return 0

    errs = 0
    for fpath in fpaths:
        if not fpath.is_file():
            errs += 1
            print(f"{fpath}: does not exist")
            continue

        with open(fpath, newline="") as f:
            reader = SectionsCsvReader(f)
            for line, msg in reader.iter_problems():
                errs += 1
                print(f"{fpath}@L{line}: {msg}")

    if errs:
        return 1
    return 0


def validate_sections_csv_cli():
    parser = ArgumentParser(description="Validate a CSV of details about sections.")
    parser.add_argument(
        "path",
        nargs="*",
        type=Path,
        default=[],
        help="path to CSV files (can give multiple)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=1,
        help="increase logging verbosity (can be given multiple times)",
    )
    args = parser.parse_args()
    log_level = {
        0: logging.WARNING,
        1: logging.INFO,
    }.get(args.verbose, logging.DEBUG)
    logging.basicConfig(level=log_level)
    sys.exit(_validate_sections_csv(args.path))
