import logging
import pathlib
from typing import Final, Generator

import elasticsearch
from elasticsearch import helpers as es_helpers

from librarian import const, logging_util

# TODO: vector search
# TODO: support PDF, epub

_LOGGER: Final[logging.Logger] = logging_util.get_logger(__name__)


def _ensure_index_exists(es_client: elasticsearch.Elasticsearch) -> None:
    if not es_client.indices.exists(index=const.ES_INDEX_NAME):
        es_client.indices.create(index=const.ES_INDEX_NAME)


def _split(text: str) -> Generator[str, None, None]:
    chunk_size = 1000
    overlap = 100
    for i in range(0, max(0, len(text) - overlap), chunk_size - overlap):
        yield text[i : i + chunk_size]


def ingest(path: pathlib.Path, elasticsearch_url: str) -> None:
    es_client = elasticsearch.Elasticsearch(elasticsearch_url)
    _ensure_index_exists(es_client)
    success, errors = es_helpers.bulk(
        es_client,
        index=const.ES_INDEX_NAME,
        actions=(
            {
                "_index": const.ES_INDEX_NAME,
                "_source": {"file_name": path.name, "content": chunk},
            }
            for chunk in _split(path.read_text())
        ),
    )
    if errors:
        _LOGGER.error("Failed to ingest document: %s", errors)
    _LOGGER.info("Successfully ingested document: %s", success)
