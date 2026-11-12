import pytest

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy


class RetryState(TypedDict):
    result: str


@pytest.mark.asyncio
async def retry_policy():

    attempts = {"count": 0}

    async def unreliable_node(state: RetryState) -> dict:
        attempts["count"] += 1

        print(f"Attempt: {attempts['count']}")

        if attempts["count"] < 3:
            raise ConnectionError("Temporary connection failure")

        return {"result": "Operation successful"}

    builder = StateGraph(RetryState)

    builder.add_node(
        "unreliable_node",
        unreliable_node,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_interval=0.1,
            backoff_factor=2.0,
            max_interval=1.0,
            jitter=False,
            retry_on=(ConnectionError,),
        ),
    )

    builder.add_edge(START, "unreliable_node")
    builder.add_edge("unreliable_node", END)

    graph = builder.compile()

    result = await graph.ainvoke({"result": ""})

    assert attempts["count"] == 3
    assert result["result"] == "Operation successful"
