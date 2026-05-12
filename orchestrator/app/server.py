import logging
import os
import json
import warnings
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from pydantic import BaseModel

from app.agent import app as adk_app

warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*", category=UserWarning)
logging.getLogger("google_adk.google.adk.runners").setLevel(logging.ERROR)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

runner = Runner(
    app=adk_app,
    artifact_service=InMemoryArtifactService(),
    session_service=InMemorySessionService(),
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimpleChatRequest(BaseModel):
    message: str
    user_id: str = "director"
    session_id: str = "default_sprint"

@app.post("/api/chat_stream")
async def chat_stream(request: SimpleChatRequest):
    try:
        session = await runner.session_service.get_session(
            session_id=request.session_id, app_name=adk_app.name, user_id=request.user_id
        )
    except Exception:
        session = None
    if not session:
        session = await runner.session_service.create_session(
            app_name=adk_app.name,
            user_id=request.user_id,
            session_id=request.session_id,
        )

    user_msg = genai_types.Content(
        role="user", parts=[genai_types.Part.from_text(text=request.message)]
    )

    async def event_generator():
        final_text = ""
        async for event in runner.run_async(
            user_id=request.user_id, session_id=session.id, new_message=user_msg
        ):
            if event.author == "developer":
                 yield json.dumps({"type": "progress", "text": "💻 Developer is generating code..."}) + "\n"
            elif event.author == "governance_gate":
                 yield json.dumps({"type": "progress", "text": "🛡️ Governance Gate checking approval..."}) + "\n"
            elif event.author == "it_engineer":
                 yield json.dumps({"type": "progress", "text": "🚀 I&T Engineer is deploying changes..."}) + "\n"
            elif event.author == "qa_auditor":
                 yield json.dumps({"type": "progress", "text": "🔎 QA Auditor is verifying deployment..."}) + "\n"

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text

        # Yield any final accumulated text from agents in the orchestrator directly
        if final_text:
            yield json.dumps({"type": "result", "text": final_text.strip()}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
os.makedirs(frontend_path, exist_ok=True)
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
