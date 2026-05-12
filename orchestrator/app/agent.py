import os
import json
import warnings
from typing import AsyncGenerator
import google.auth
from google.adk.agents import BaseAgent, LoopAgent, SequentialAgent
from google.adk.apps.app import App
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.callback_context import CallbackContext

warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*", category=UserWarning)

try:
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
except Exception:
    pass

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

def create_save_output_callback(key: str):
    def callback(callback_context: CallbackContext, **kwargs) -> None:
        ctx = callback_context
        for event in reversed(ctx.session.events):
            if event.author == ctx.agent_name and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    if key == "qa_feedback" and text.strip().startswith("{"):
                        try:
                            ctx.state[key] = json.loads(text)
                        except json.JSONDecodeError:
                            ctx.state[key] = text
                    else:
                        ctx.state[key] = text
                    print(f"[{ctx.agent_name}] Saved output to state['{key}']")
                    return
    return callback

developer_url = os.environ.get("DEVELOPER_AGENT_CARD_URL", "http://localhost:8001/.well-known/agent.json")
developer = RemoteA2aAgent(
    name="developer",
    agent_card=developer_url,
    description="Generates proposed code changes based on user intent.",
    after_agent_callback=create_save_output_callback("proposed_changes")
)

it_engineer_url = os.environ.get("IT_ENGINEER_AGENT_CARD_URL", "http://localhost:8002/.well-known/agent.json")
it_engineer = RemoteA2aAgent(
    name="it_engineer",
    agent_card=it_engineer_url,
    description="Deploys the proposed code changes.",
    after_agent_callback=create_save_output_callback("it_logs")
)

qa_auditor_url = os.environ.get("QA_AUDITOR_AGENT_CARD_URL", "http://localhost:8003/.well-known/agent.json")
qa_auditor = RemoteA2aAgent(
    name="qa_auditor",
    agent_card=qa_auditor_url,
    description="Verifies the deployment matches the golden state requirements.",
    after_agent_callback=create_save_output_callback("qa_feedback")
)

class GovernanceGate(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        proposed = ctx.session.state.get("proposed_changes")
        approved = ctx.session.state.get("director_approval")
        
        # Check if the user message itself is an approval
        user_message = ""
        for event in reversed(ctx.session.events):
            if event.author == "user" and event.content and event.content.parts:
                user_message = event.content.parts[0].text.strip().lower()
                break
                
        if user_message == "approved" or user_message == "approve":
            ctx.session.state["director_approval"] = True
            approved = True

        if not approved:
            # Yield a message to the user asking for approval, and suspend execution
            msg = "The Developer has proposed the following changes:\n\n"
            msg += str(proposed)
            msg += "\n\nDo you authorize this Maintenance Window? Please respond with 'APPROVED' to continue."
            yield Event(author=self.name, content={"role": "agent", "parts": [{"text": msg}]})
            # To pause and return to the user, we can yield an action. 
            # In a loop, if we don't escalate, it goes to the next agent.
            # To stop it proceeding to it_engineer, we might need a condition or a way to abort this loop iteration.
            # For simplicity, we just skip it_engineer if not approved. Wait, we can't easily skip in a basic Sequential.
            # Let's escalate to break out of the IT/QA flow until approved.
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name, content={"role": "agent", "parts": [{"text": "Director approval confirmed. Proceeding to deployment."}]})

governance_gate = GovernanceGate(name="governance_gate")

class QAEscalationChecker(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        feedback = ctx.session.state.get("qa_feedback")

        if feedback and isinstance(feedback, dict) and feedback.get("status") == "pass":
            yield Event(author=self.name, content={"role": "agent", "parts": [{"text": "Sprint complete! QA passed."}]})
            yield Event(author=self.name, actions=EventActions(escalate=True))
        elif isinstance(feedback, str) and '"status": "pass"' in feedback.lower():
            yield Event(author=self.name, content={"role": "agent", "parts": [{"text": "Sprint complete! QA passed."}]})
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            # Clear director approval so it asks again if we loop back
            ctx.session.state["director_approval"] = False
            yield Event(author=self.name, content={"role": "agent", "parts": [{"text": "QA failed. Looping back to Developer."}]})

qa_escalation_checker = QAEscalationChecker(name="qa_escalation_checker")

# Full sprint loop
sprint_loop = LoopAgent(
    name="sprint_loop",
    description="Iteratively develops, deploys, and audits until the QA passes.",
    sub_agents=[developer, governance_gate, it_engineer, qa_auditor, qa_escalation_checker],
    max_iterations=5,
)

app = App(root_agent=sprint_loop, name="lead_engineer")
