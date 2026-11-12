from langgraph.types import RetryPolicy
from langgraph.graph import StateGraph, START, END

from app.graphs.state import IncidentState
from app.graphs.nodes import (
    investigate_incident, generate_incident_report,
    review_investigation, route_investigation,
    generate_inconclusive_report, prepare_remediation,
    request_human_approval, execute_remediation,
    skip_remediation, route_approval, handle_investigation_error,
    handle_investigation_failure
)


def create_incident_workflow(checkpointer=None):
    builder = StateGraph(IncidentState)
    builder.add_node(
        "investigate_incident",
        investigate_incident,
        retry_policy=RetryPolicy(
            max_attempts=3,
            initial_interval=1.0,
            backoff_factor=2.0,
            max_interval=10.0,
            jitter=True,
            retry_on=(TimeoutError, ConnectionError)
        ),
        error_handler=handle_investigation_error
    )
    builder.add_node("generate_incident_report", generate_incident_report)
    builder.add_node("review_investigation", review_investigation)
    builder.add_node("generate_inconclusive_report", generate_inconclusive_report)
    builder.add_node("prepare_remediation", prepare_remediation)
    builder.add_node("request_human_approval", request_human_approval)
    builder.add_node("execute_remediation", execute_remediation)
    builder.add_node("skip_remediation", skip_remediation)
    builder.add_node(
        "handle_investigation_failure",
        handle_investigation_failure,
    )

    builder.add_edge(START, "investigate_incident")
    builder.add_edge("investigate_incident", "review_investigation")
    builder.add_conditional_edges(
        "review_investigation",
        route_investigation,
        {
            "prepare_remediation": "prepare_remediation",
            "inconclusive_report": "generate_inconclusive_report"
        }
    )
    builder.add_edge("prepare_remediation", "request_human_approval")
    builder.add_conditional_edges(
        "request_human_approval",
        route_approval,
        {
            "execute_remediation": "execute_remediation",
            "skip_remediation": "skip_remediation"
        }
    )
    builder.add_edge(
        "handle_investigation_failure",
        "generate_inconclusive_report",
    )
    builder.add_edge("execute_remediation", "generate_incident_report")
    builder.add_edge("skip_remediation", "generate_incident_report")
    builder.add_edge("generate_incident_report", END)
    builder.add_edge("generate_inconclusive_report", END)
    graph = builder.compile(checkpointer=checkpointer)
    return graph
