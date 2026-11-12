import pytest

from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

from app.graphs.state import IncidentState
from app.graphs.nodes import handle_investigation_error


@pytest.mark.asyncio
async def test_investigation_failure_handling():

    attempts = {"count": 0}

    async def failing_investigation(state: IncidentState) -> dict:
        attempts["count"] += 1

        print(f"Investigation attempt: {attempts['count']}")

        raise ConnectionError("Database connection unavailable")

    def failure_node(state: IncidentState) -> dict:
        print("Failure handler executed")

        return {
            "investigation_result": (
                f"Investigation failed: {state['error_message']}"
            )
        }

    builder = StateGraph(IncidentState)

    builder.add_node(
        "investigate_incident",
        failing_investigation,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_interval=0.1,
            backoff_factor=2.0,
            max_interval=1.0,
            jitter=False,
            retry_on=(ConnectionError,),
        ),
        error_handler=handle_investigation_error,
    )

    builder.add_node(
        "handle_investigation_failure",
        failure_node,
    )

    builder.add_edge(START, "investigate_incident")
    builder.add_edge("handle_investigation_failure", END)

    graph = builder.compile()

    initial_state = {
        "incident_id": "INC-FAIL-1001",
        "service_name": "payment-api",
        "incident_description": "Payment API is returning HTTP 503.",
        "investigation_result": "",
        "investigation_status": "",
        "remediation_action": "",
        "approval_status": "",
        "remediation_result": "",
        "final_report": "",
        "error_message": "",
    }

    result = await graph.ainvoke(initial_state)

    print("\nFinal state:", result)

    assert attempts["count"] == 3
    assert result["investigation_status"] == "failed"
    assert "Database connection unavailable" in result["error_message"]
    assert "Remediation was not attempted" in result["remediation_result"]
    assert "Investigation failed" in result["investigation_result"]
