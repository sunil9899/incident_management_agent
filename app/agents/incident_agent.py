from langchain.agents import create_agent

from app.core.llm import get_llm
from app.tools.registry import INCIDENT_TOOLS


SYSTEM_PROMPTS = """
You are an AI Incident Investigation Agent.

Your responsibility is to investigate backend application incidents.

Instructions:

1. Understand the reported incident.
2. Select relevant diagnostic tools.
3. Analyze actual tool results.
4. Never invent diagnostic findings.
5. Distinguish confirmed findings from hypotheses.
6. Do not perform remediation without authorization.
7. Avoid unnecessary repeated tool calls.
"""


def create_incident_agent():
    llm = get_llm()
    agent = create_agent(
        model=llm,
        tools=INCIDENT_TOOLS,
        system_prompt=SYSTEM_PROMPTS
    )
    return agent
