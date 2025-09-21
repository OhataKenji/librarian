import argparse
import pathlib
from typing import Final

from librarian import agent, ingester

# TODO: make Elasticsearch host configurable
_ELASTICSEARCH_URL: Final[str] = "http://localhost:9200"


def _handle_ask(query: str) -> None:
    print(
        agent.libralian_agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
        )["messages"][-1].content
    )


def _handle_ingest(path: pathlib.Path) -> None:
    ingester.ingest(path, _ELASTICSEARCH_URL)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a question to the librarian")
    ask_parser.add_argument("query", type=str, help="Query")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("path", type=pathlib.Path, help="Path to the document")

    args = parser.parse_args()
    match args.command:
        case "ask":
            _handle_ask(args.query)
        case "ingest":
            _handle_ingest(args.path)


if __name__ == "__main__":
    main()
