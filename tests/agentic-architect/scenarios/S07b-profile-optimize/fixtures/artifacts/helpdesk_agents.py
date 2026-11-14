# Pilot build of the acme helpdesk (S02 design), OpenAI Agents SDK, Python.
from agents import Agent, FileSearchTool, Runner, function_tool
from pydantic import BaseModel


class PolicyAnswer(BaseModel):
    answer: str
    page_citations: list[str]
    confidence: str  # high | medium | low


@function_tool
def create_ticket(summary: str, body: str, team: str) -> str:
    """Create a Jira ticket for HR. Reversible: tickets can be closed."""
    ...


policy_answer = Agent(
    name="policy_answer",
    instructions=(
        "Answer the employee's HR question from the policy pages returned by file search. "
        "Give the short answer first, then the policy basis with a link to the page, then next steps. "
        "Never change payroll data; if asked, say that Payroll handles it via the Payroll form. "
        "If the pages do not cover the question, say so and set confidence to low."
    ),
    tools=[FileSearchTool(vector_store_ids=["vs_hr_policy_2026q4"], max_num_results=5)],
    output_type=PolicyAnswer,
    model="gpt-5",
)

ticket = Agent(
    name="ticket",
    instructions="Open a Jira ticket summarising the employee's question for the right HR team and tell the employee the ticket number.",
    tools=[create_ticket],
    model="gpt-5-mini",
)

triage = Agent(
    name="triage",
    instructions=(
        "Decide whether the employee's message is a policy question (hand off to policy_answer), "
        "a personal-record or payroll matter (hand off to ticket), or small talk (answer briefly)."
    ),
    handoffs=[policy_answer, ticket],
    model="gpt-5-mini",
)
