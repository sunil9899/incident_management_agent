import pytest

from langgraph.types import Command
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings
from app.graphs.workflow import create_incident_workflow


@pytest.mark.asyncio
@pytest.mark.parametrize("approved", [True, False])
async def human_approval(approved: bool):
    settings = get_settings()

    checkpointer_url = (
        settings.database_url
        .render_as_string(hide_password=False)
        .replace("postgresql+asyncpg://", "postgresql://", 1)
    )

    initial_state = {
        "incident_id": f"INC-APPROVAL-{approved}",
        "service_name": "payment-api",
        "incident_description": (
            "Payment API is returning HTTP 503 errors."
        ),
        "investigation_result": "",
        "investigation_status": "",
        "remediation_action": "",
        "approval_status": "",
        "remediation_result": "",
        "final_report": "",
    }

    async with AsyncPostgresSaver.from_conn_string(
        checkpointer_url
    ) as checkpointer:

        await checkpointer.setup()

        graph = create_incident_workflow(
            checkpointer=checkpointer
        )

        config = {
            "configurable": {
                "thread_id": f"INC-APPROVAL-{approved}"
            }
        }

        # Start investigation and wait for human approval.
        paused_result = await graph.ainvoke(
            initial_state,
            config=config,
        )

        # Verify that the workflow was interrupted.
        # assert paused_result.get("__interrupt__")

        # assert (
        #     paused_result["approval_status"] == "pending"
        # )
        #
        # assert paused_result["remediation_result"] == ""

        snapshot = await graph.aget_state(config)

        print("\n--- CHECKPOINT STATE ---")
        print(snapshot.values)

        print("\n--- NEXT NODES ---")
        print(snapshot.next)

        print("\n--- INTERRUPT TASKS ---")
        print(snapshot.tasks)

        assert snapshot.values["approval_status"] == "pending"
        assert snapshot.values["remediation_result"] == ""
        assert snapshot.next

        # Resume the same workflow with human input.
        final_result = await graph.ainvoke(
            Command(resume={"approved": approved}),
            config=config,
        )

        if approved:
            assert final_result["approval_status"] == "approved"
            assert "Mock remediation executed" in (
                final_result["remediation_result"]
            )
        else:
            assert final_result["approval_status"] == "rejected"
            assert "Remediation rejected" in (
                final_result["remediation_result"]
            )

        assert final_result["final_report"]
