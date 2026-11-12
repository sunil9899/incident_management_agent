from app.agents.incident_agent import create_incident_agent
from app.graphs.state import IncidentState
from app.core.llm import get_llm
from langgraph.types import interrupt, Command
from langgraph.errors import NodeError


incident_agent = create_incident_agent()
llm = get_llm()


async def investigate_incident(state: IncidentState) -> dict:
    """
    Execute the incident investigation using the LangChain Agent
    """
    response = await incident_agent.ainvoke({
        "messages": [{
            "role": "user",
            "content": (
                "Investigate the following incident:\n"
                f"Incident ID: {state['incident_id']}\n"
                f"Service: {state['service_name']}"
                f"Description: {state['incident_description']}"
            )
        }]
    })
    final_message = response["messages"][-1]
    return {
        "investigation_result": final_message.content
    }


async def generate_incident_report(state: IncidentState) -> dict:
    """
    Generate a structured incident report from investigation findings.
    """
    prompt = f"""
Generate a structured incident report using following information.

Incident ID: {state["incident_id"]}
Service: {state["service_name"]}
Investigation Description: {state["incident_description"]}

Investigation Findings:
{state["investigation_result"]}

Include the following sections:
1. Incident Summary
2. Investigation Findings
3. Probable Root Cause
4. Recommended Action
5. Incident Severity

Do not invent findings that are not supported by the investigation.
Clearly identify any unknown information.
"""
    response = await llm.ainvoke(prompt)
    return {"final_report": response.content}


async def review_investigation(state: IncidentState) -> dict:
    """
    Determine whether sufficient diagnostic evidence was collected.
    """

    investigation_result = state["investigation_result"]

    if investigation_result and investigation_result.strip():
        return {"investigation_status": "completed"}

    return {"investigation_status": "inconclusive"}


def route_investigation(state: IncidentState) -> str:
    """Route the workflow based on investigation status."""
    if state["investigation_status"] == "completed":
        return "prepare_remediation"
    return "inconclusive_report"


def route_approval(state: IncidentState) -> str:
    if state["approval_status"] == "approved":
        return "execute_remediation"
    return "skip_remediation"


def generate_inconclusive_report(state: IncidentState) -> dict:
    """Generate a report when investigation is sufficient."""
    return {
        "final_report": (
            f"Incident ID: {state['incident_id']}\n"
            f"Service: {state['service_name']}\n"
            "Status: Investigation inconclusive\n"
            f"Findings: {state['investigation_result']}\n"
            "Further investigation is required."
        )
    }


def request_human_approval(state: IncidentState) -> dict:
    """
    Pause the workflow and request human approval
    before executing a remedial action.
    """
    approval = interrupt({
        "incident_id": state["incident_id"],
        "service_name": state["service_name"],
        "proposed_action": state["remediation_action"],
        "message": "Please approve or reject this remediation action."
    })
    if not isinstance(approval, dict):
        return {"approval_status": "rejected"}
    if approval.get("approved") is True:
        return {"approval_status": "approved"}
    return {"approval_status": "rejected"}


def prepare_remediation(state: IncidentState) -> dict:
    """
    Prepare a remediation proposal based on the investigation.
    This function does not execute the action.
    """
    return {
        "remediation_action": (
            f"Restart the {state['service_name']} service "
            "after verifying operational impact."
        ),
        "approval_status": "pending",
        "remediation_result": "",
    }


def execute_remediation(state: IncidentState) -> dict:
    """
    Execute a mock remediation after human approval.
    No real infrastructure changes are performed.
    """
    return {
        "remediation_result": (
            f"Mock remediation executed: "
            f"{state['remediation_action']}"
        )
    }


def skip_remediation(state: IncidentState) -> dict:
    """
    Skip remediation when human approval is rejected.
    """

    return {
        "remediation_result": (
            f"Remediation rejected by human reviewer: "
            f"{state['remediation_action']}"
        )
    }


def handle_investigation_failure(state: IncidentState) -> dict:
    """
    Record the final investigation failure.
    """

    return {
        "investigation_result": (
            f"Investigation could not be completed. "
            f"Error details: {state['error_message']}"
        )
    }


def handle_investigation_error(
    state: IncidentState,
    error: NodeError,
) -> Command:
    """
    Handle investigation failure after retry attempts are exhausted.
    """
    return Command(
        update={
            "investigation_status": "failed",
            "error_message": (
                f"Node: {error.node}. Error: {error.error}"
            ),
            "remediation_result": (
                "Remediation was not attempted because "
                "investigation failed."
            ),
        },
        goto="handle_investigation_failure",
    )
