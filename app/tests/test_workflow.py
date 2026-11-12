import asyncio
import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings
from app.graphs.workflow import create_incident_workflow


@pytest.mark.asyncio
async def main() -> None:
    settings = get_settings()
    checkpointer_url = (
        settings.database_url
        .render_as_string(hide_password=False)
        .replace("postgresql+asyncpg://", "postgresql://", 1)
    )
    async with AsyncPostgresSaver.from_conn_string(
        checkpointer_url
    ) as checkpointer:
        await checkpointer.setup()
        graph = create_incident_workflow(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": "INC-1001"
            }
        }
        initial_state = {
            "incident_id": "INC-1001",
            "service_name": "payment-api",
            "incident_description": "Payment API is returning HTTP 503 errors.",
            "investigation_result": "",
            "final_report": ""
        }
        response = await graph.ainvoke(
            initial_state,
            config=config
        )
        print(f"Investigation Result:\n{response['investigation_result']}")
        print(f"Final Report:\n{response['final_report']}")
        snapshot = await graph.aget_state(config=config)
        print(f"\nPersisted state: {snapshot.values}")
        print(f"\nNext nodes: {snapshot.next}")


if __name__ == "__main__":
    asyncio.run(test_main())
