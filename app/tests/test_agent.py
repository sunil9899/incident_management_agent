import pytest
from app.agents.incident_agent import create_incident_agent


@pytest.mark.asyncio
async def main():
    """To test the agent"""
    agent = create_incident_agent()
    response = await agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": (
                "Investigate why the Payment API "
                "is returning HTTP 503 errors. "
                "Find the probable root cause."
            )
        }]
    })
    for message in response["messages"]:
        print(f"\n{message.type}-->>\n{message.content}")
