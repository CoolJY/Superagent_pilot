"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""

import os
import warnings

from dotenv import load_dotenv
from src.deployment import air_gap_enabled, server_model_enabled

load_dotenv()
if air_gap_enabled() or server_model_enabled():
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["COPILOTKIT_TELEMETRY_DISABLED"] = "true"
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from copilotkit import CopilotKitMiddleware
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from deepagents import create_deep_agent

from src.anthropic_compat import ConsecutiveSystemMessagesMiddleware
from src.bounded_memory_saver import BoundedMemorySaver
from src.model import build_model, RequestModelMiddleware, CredentialScopedModel
from src.credentials import (
    CredentialsMiddleware,
    CredentialScopedAgent,
    current_credentials,
    validate_credentials,
)
from src.visualization_router import JevVisualizationMiddleware
from src.skill_backend import SKILL_SOURCES, build_agent_backend
from src.query import query_data
from src.todos import AgentState, todo_tools
from src.form import generate_form
from src.trip_images import get_trip_stop_images
from src.plan import plan_visualization
from src.prompt import SYSTEM_PROMPT, AIR_GAP_PROMPT, SERVER_MODEL_PROMPT

agent = create_deep_agent(
    model=CredentialScopedModel(fallback=build_model(allow_unconfigured=True)),
    tools=[query_data, plan_visualization, *todo_tools, generate_form,
           *([] if air_gap_enabled() or server_model_enabled() else [get_trip_stop_images])],
    middleware=[
        RequestModelMiddleware(),
        CopilotKitMiddleware(),
        *([] if air_gap_enabled() or server_model_enabled() else [JevVisualizationMiddleware()]),
        ConsecutiveSystemMessagesMiddleware(),
    ],
    context_schema=AgentState,
    skills=SKILL_SOURCES,
    backend=build_agent_backend,
    checkpointer=BoundedMemorySaver(max_threads=200),
    system_prompt=(AIR_GAP_PROMPT if air_gap_enabled() else
                   SERVER_MODEL_PROMPT if server_model_enabled() else SYSTEM_PROMPT),
)

app = FastAPI()
app.add_middleware(CredentialsMiddleware)


@app.post("/credentials/validate")
async def validate_provider_credentials():
    credentials = current_credentials.get()
    if credentials is None:
        return JSONResponse({"ok": False, "code": "invalid_keys"}, status_code=400)
    return await validate_credentials(credentials)


@app.get("/health")
def health():
    return {"status": "ok"}


add_langgraph_fastapi_endpoint(
    app=app,
    agent=CredentialScopedAgent(
        name="sample_agent",
        description="Open Generative UI by CopilotKit — answers you can interact with",
        graph=agent,
    ),
    path="/",
)

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8123"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
