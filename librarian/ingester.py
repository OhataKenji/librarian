import logging
import pathlib
from typing import Final, Generator

import elasticsearch
import markitdown
from elasticsearch import helpers as es_helpers

from librarian import const, logging_util
from librarian.embedding import get_embedding_model

# TODO: vector search
# TODO: support PDF, epub

_LOGGER: Final[logging.Logger] = logging_util.get_logger(__name__)


def _ensure_index_exists(es_client: elasticsearch.Elasticsearch) -> None:
    if not es_client.indices.exists(index=const.ES_INDEX_NAME):
        mapping = {
            "mappings": {
                "properties": {
                    "file_name": {"type": "text"},
                    "content": {"type": "text"},
                    "content_vector": {
                        "type": "dense_vector",
                        "dims": 2048,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        es_client.indices.create(index=const.ES_INDEX_NAME, body=mapping)
        _LOGGER.info(f"Created index {const.ES_INDEX_NAME} with vector mapping")
    else:
        _LOGGER.info(f"Index {const.ES_INDEX_NAME} already exists")


def _split(text: str) -> Generator[str, None, None]:
    chunk_size = 1000
    overlap = 100
    for i in range(0, max(0, len(text) - overlap), chunk_size - overlap):
        yield text[i : i + chunk_size]


def _extract_chunks(path: pathlib.Path) -> Generator[str, None, None]:
    # TODO: detect filetype according to its content
    if path.suffix == ".pdf":
        md = markitdown.MarkItDown(enable_plugins=True)
        result = md.convert(path)
        yield from _split(result.text_content)
    elif path.suffix == ".txt":
        yield from _split(path.read_text())
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def ingest(path: pathlib.Path, elasticsearch_url: str) -> None:
    es_client = elasticsearch.Elasticsearch(elasticsearch_url)
    _ensure_index_exists(es_client)
    
    embedding_model = get_embedding_model()
    
    def generate_actions():
        for chunk in _extract_chunks(path):
            try:
                content_vector = embedding_model.encode_document(chunk)
                yield {
                    "_index": const.ES_INDEX_NAME,
                    "_source": {
                        "file_name": path.name,
                        "content": chunk,
                        "content_vector": content_vector
                    },
                }
            except Exception as e:
                _LOGGER.error(f"Failed to generate embedding for chunk: {e}")
                yield {
                    "_index": const.ES_INDEX_NAME,
                    "_source": {"file_name": path.name, "content": chunk},
                }
    
    success, errors = es_helpers.bulk(es_client, actions=generate_actions())
    if errors:
        _LOGGER.error("Failed to ingest document: %s", errors)
    _LOGGER.info("Successfully ingested document: %s", success)
