from typing import TypedDict


class IncidentState(TypedDict):
    incident_id: str
    service_name: str
    incident_description: str
    investigation_result: str
    final_report: str
    investigation_status: str
    remediation_action: str
    approval_status: str
    remediation_result: str
    error_message: str
