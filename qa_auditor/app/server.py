import os
import logging
from starlette.middleware.cors import CORSMiddleware
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from app.agent import app as adk_app

PORT = 8003

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

a2a_app = to_a2a(adk_app.root_agent, port=PORT)

app = CORSMiddleware(
    app=a2a_app,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
