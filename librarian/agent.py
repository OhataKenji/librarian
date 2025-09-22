import os

import elasticsearch
from librarian import const
from librarian.embedding import get_embedding_model
from langchain_google_genai import ChatGoogleGenerativeAI
import langfuse.langchain
from langgraph.prebuilt import create_react_agent
from typing import Any

def _get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY"], temperature=0
    )


def _markup_chunk(chunk: dict[str, Any]) -> str:
    return f"Chunk From: {chunk['_source']['file_name']}\n{chunk['_source']['content']}"


def _markup_chunks(chunks: list[dict[str, Any]]) -> str:
    max_chunk_to_read = 10
    return "\n\n".join(_markup_chunk(chunk) for chunk in chunks[:max_chunk_to_read])


def _search(query: str) -> str:
    """Search for the given query using hybrid text and vector search."""
    es = elasticsearch.Elasticsearch(const.ES_URL)
    
    try:
        embedding_model = get_embedding_model()
        query_vector = embedding_model.encode_query(query)
        
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"content": query}},
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                                    "params": {"query_vector": query_vector}
                                }
                            }
                        }
                    ]
                }
            }
        }
    except Exception:
        search_body = {"query": {"match": {"content": query}}}
    
    res = es.search(index=const.ES_INDEX_NAME, body=search_body)
    return _markup_chunks(res["hits"]["hits"])


def get_libralian_agent():
    return create_react_agent(
        model=_get_llm(),
        tools=[_search],
        prompt="あなたはQ&Aアシスタントです。ユーザーの質問に応えるために、検索結果を基に回答してください。検索対象のドキュメントは日本語と英語が中心です。日本語と英語で検索してください。",
    ).with_config({"callbacks": [langfuse.langchain.CallbackHandler()]})
