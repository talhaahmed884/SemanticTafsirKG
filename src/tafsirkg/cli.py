"""Command line interface.

``tafsirkg inventory <folder>`` lists the elements and attribute values in a folder.
``tafsirkg build <folder>``     converts a folder into ``<name>.ttl`` + ``<name>.issues.csv``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from tafsirkg.issues import IssueLog
from tafsirkg.pipeline import KnowledgeGraphBuilder, read_documents, write_outputs
from tafsirkg.rdf.iris import DEFAULT_BASE_IRI
from tafsirkg.tei.inventory import TeiInventory

DEFAULT_OUTPUT_DIR = Path("KnowledgeGraph")


def _folder(value: str) -> Path:
    path = Path(value)
    if not path.is_dir():
        raise argparse.ArgumentTypeError(f"not a folder: {value}")
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tafsirkg", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    inventory = commands.add_parser("inventory", help="list elements and attribute values")
    inventory.add_argument("folders", nargs="+", type=_folder, help="surah folder(s), e.g. Dataset/S001M")

    build = commands.add_parser("build", help="convert surah folder(s) into RDF")
    build.add_argument("folders", nargs="+", type=_folder, help="surah folder(s), e.g. Dataset/S001M")
    build.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT_DIR, help="output folder")
    build.add_argument("--base-iri", default=DEFAULT_BASE_IRI, help="base IRI of generated resources")
    return parser


def _inventory(folders: Sequence[Path]) -> int:
    issues = IssueLog()
    inventory = TeiInventory()
    for folder in folders:
        inventory.add_documents(read_documents(folder, issues))
    print(inventory.render())
    for issue in issues:
        print(f"{issue.severity}: {issue.source}: {issue.message}", file=sys.stderr)
    return 0


def _build(folders: Sequence[Path], output: Path, base_iri: str) -> int:
    builder = KnowledgeGraphBuilder(base_iri=base_iri)
    for folder in folders:
        result = builder.build(folder)
        graph_path, issues_path = write_outputs(result, output)
        print(f"== {result.name}\n{result.summary()}\nwrote {graph_path} and {issues_path}\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "inventory":
        return _inventory(args.folders)
    return _build(args.folders, args.output, args.base_iri)


if __name__ == "__main__":
    sys.exit(main())
