"""Market-intelligence brief pipeline. OpenAI Agents SDK.

Frozen for this run: orchestrator, triage, drafter, reviewer, the handoff graph.
In scope: researcher only.
"""
from agents import Agent, FileSearchTool, Runner, WebSearchTool, function_tool, handoff
from pydantic import BaseModel


# ---- shared schemas ---------------------------------------------------------

class TriageDecision(BaseModel):
    klass: str            # lookup | investigate | decline
    reason: str
    owner: str            # researcher | drafter


class Brief(BaseModel):
    headline: str
    findings: list[str]
    implication: str
    sources: list[str]


class ReviewResult(BaseModel):
    verdict: str          # pass | fix
    fixes: list[str]


# ---- agents -----------------------------------------------------------------

triage = Agent(
    name="triage",
    instructions=(
        "Classify the research request as lookup, investigate, or decline. "
        "Lookup when the notes repository already answers it; investigate when new research is needed; "
        "decline when it is not market intelligence. Return the class, a one-line reason, and the owner."
    ),
    output_type=TriageDecision,
    model="gpt-5-mini",
)

researcher = Agent(
    name="researcher",
    instructions=(
        "You are a market researcher. Find out everything relevant about the question. "
        "Use the notes and the web. Be thorough. Do not make things up. "
        "Return your findings."
    ),
    tools=[WebSearchTool()],
    model="gpt-5",
)

drafter = Agent(
    name="drafter",
    instructions=(
        "Write the client brief from the researcher's findings: headline, three cited findings, "
        "implication, sources. Two pages maximum. Every claim must carry a citation from the findings."
    ),
    output_type=Brief,
    model="gpt-5",
)

reviewer = Agent(
    name="reviewer",
    instructions=(
        "Check the brief against the findings: every claim cited and supported, house structure, "
        "neutral tone, length. Return pass, or a list of required fixes naming sentence, problem and fix."
    ),
    output_type=ReviewResult,
    model="gpt-5",
)

orchestrator = Agent(
    name="orchestrator",
    instructions=(
        "Run the pipeline: triage the request; if investigate, call the researcher then the drafter; "
        "if lookup, call the drafter with the notes; then call the reviewer. If the reviewer returns fixes, "
        "send them to the drafter once, then review again. Return the final brief and the review verdict."
    ),
    tools=[
        triage.as_tool(tool_name="triage", tool_description="Classify the request."),
        researcher.as_tool(tool_name="research", tool_description="Research the question and return findings."),
        drafter.as_tool(tool_name="draft", tool_description="Draft the brief from findings."),
        reviewer.as_tool(tool_name="review", tool_description="Review the brief against the findings."),
    ],
    model="gpt-5",
)


async def run(request: str):
    return await Runner.run(orchestrator, request)
