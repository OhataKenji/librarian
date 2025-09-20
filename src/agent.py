from typing import Annotated
from langchain_openai import ChatOpenAI
from langgraph import StateGraph
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

def call_model(state: MessagesState):
    model = ChatOpenAI(model="gpt-4")
    response = model.invoke(state["messages"])
    return {"messages": [response]}

workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)

workflow.set_entry_point("agent")
workflow.set_finish_point("agent")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
