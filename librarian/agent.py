import os

import elasticsearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY"], temperature=0
)


def _search(query: str) -> str:
    """Search for the given query."""
    es = elasticsearch.Elasticsearch()
    res = es.search(index="documents", body={"query": {"match": {"content": query}}})
    return res["hits"]["hits"][0]["_source"]["content"]


libralian_agent = create_react_agent(
    model=_llm,
    tools=[_search],
    prompt="You are a Q&A assistant. Answer the user's question based on search results.",
)
