import os

import elasticsearch
from librarian import const
from langchain_google_genai import ChatGoogleGenerativeAI
import langfuse.langchain
from langgraph.prebuilt import create_react_agent
from typing import Any

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY"], temperature=0
)


def _markup_chunk(chunk: dict[str, Any]) -> str:
    return f"Chunk From: {chunk['_source']['file_name']}\n{chunk['_source']['content']}"


def _markup_chunks(chunks: list[dict[str, Any]]) -> str:
    max_chunk_to_read = 10
    return "\n\n".join(_markup_chunk(chunk) for chunk in chunks[:max_chunk_to_read])


def _search(query: str) -> str:
    """Search for the given query."""
    es = elasticsearch.Elasticsearch(const.ES_URL)
    res = es.search(
        index=const.ES_INDEX_NAME, body={"query": {"match": {"content": query}}}
    )
    return _markup_chunks(res["hits"]["hits"])


libralian_agent = create_react_agent(
    model=_llm,
    tools=[_search],
    prompt="あなたはQ&Aアシスタントです。ユーザーの質問に応えるために、検索結果を基に回答してください。検索対象のドキュメントは日本語と英語が中心です。日本語と英語で検索してください。",
).with_config({"callbacks": [langfuse.langchain.CallbackHandler()]})
