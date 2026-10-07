"""
Swarms SEO Office Runtime — a Claw3D "custom" runtime adapter backed by Swarms AI.

Implements the direct HTTP runtime seam Claw3D probes for:
  GET  /health
  GET  /state
  GET  /registry
  POST /v1/chat/completions

The SEO team is defined in AGENTS below: each key of /state.active becomes an
agent (worker) in the Claw3D 3D office, and POST /v1/chat/completions routes
messages to the matching Swarms agent.
"""

import os
import time
import uuid
from threading import Semaphore
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

try:
    import swarms
    from swarms import Agent

    SWARMS_AVAILABLE = True
    SWARMS_VERSION = getattr(swarms, "__version__", "unknown")
except Exception as import_error:  # pragma: no cover - surfaced via /health
    SWARMS_AVAILABLE = False
    SWARMS_VERSION = f"unavailable ({import_error})"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = os.environ.get("SWARMS_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
MODELS = [
    m.strip()
    for m in os.environ.get(
        "SWARMS_MODELS", "gpt-4o-mini,gpt-4o,gpt-4.1-mini,gpt-4.1"
    ).split(",")
    if m.strip()
]
if DEFAULT_MODEL not in MODELS:
    MODELS.insert(0, DEFAULT_MODEL)

MAX_CONCURRENT_RUNS = int(os.environ.get("SWARMS_MAX_CONCURRENT_RUNS", "2"))
MAX_LOOPS = int(os.environ.get("SWARMS_MAX_LOOPS", "1"))

RUNTIME_NAME = os.environ.get("SWARMS_RUNTIME_NAME", "Swarms AI")
RUNTIME_VENDOR = "kyegomez/swarms"

# ---------------------------------------------------------------------------
# The SEO team: /state.active keys become Claw3D office agents.
# Keep uppercase acronyms in the keys so Claw3D title-cases them nicely.
# ---------------------------------------------------------------------------

AGENTS: Dict[str, str] = {
    "SEO-Director": (
        "You are the SEO Director leading a full SEO team. You own the overall "
        "search strategy: prioritizing keywords, assigning work to the research, "
        "content, technical, marketing and link-building specialists, and turning "
        "their findings into a single action plan. When asked something, decide "
        "which part of the team should own it, lay out the plan with owners and "
        "next steps, and give a concise executive summary."
    ),
    "SEO-Research-Analyst": (
        "You are the SEO Research Analyst. You run keyword research, SERP "
        "analysis, competitor gap analysis and search-intent classification. You "
        "deliver keyword clusters with intent, difficulty and opportunity notes, "
        "plus content gaps the team should exploit. Be concrete: list keywords, "
        "angle, and why they matter."
    ),
    "Content-Writer": (
        "You are the Content Writer on the SEO team. You turn keyword research "
        "into content briefs, outlines, headings, meta titles and descriptions, "
        "and ready-to-publish drafts optimized for search intent. Deliver "
        "structured outlines and copy, with target keywords placed naturally."
    ),
    "Technical-SEO-Engineer": (
        "You are the Technical SEO Engineer. You handle crawlability, indexation, "
        "site architecture, robots.txt, XML sitemaps, canonical tags, structured "
        "data/schema, Core Web Vitals and site speed. You are also the team's "
        "software engineer: when code is needed (scripts, audits, automation), "
        "write clean, working code with brief explanations."
    ),
    "Marketing-Strategist": (
        "You are the Marketing Strategist on the SEO team. You design the "
        "go-to-market side: content distribution, social amplification, email "
        "nurture, positioning and launch campaigns that feed organic growth. "
        "Deliver channel plans with concrete steps and example copy."
    ),
    "Link-Builder": (
        "You are the Link Building Analyst. You plan backlink strategy: prospect "
        "discovery, digital PR angles, guest posting, broken-link and unlinked-"
        "mention opportunities, and outreach sequences. Deliver prospect lists "
        "with fit reasoning plus ready-to-send outreach templates."
    ),
}

FALLBACK_SYSTEM_PROMPT = (
    "You are a member of a full SEO team (strategy, research, content, "
    "technical engineering, marketing and link building). Answer your assigned "
    "task with focused, actionable SEO expertise."
)

SHARED_INSTRUCTIONS = (
    "Keep answers focused and actionable. Use short headings and bullet lists "
    "where helpful. If you need more context, state exactly what you need."
)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Swarms SEO Office Runtime", version="1.0.0")
_RUN_SEMAPHORE = Semaphore(MAX_CONCURRENT_RUNS)


def _agent_role(role: Optional[str], lane: Optional[str]) -> str:
    value = (lane or role or "main").strip()
    return value or "main"


def _system_prompt_for(role: str) -> str:
    base = AGENTS.get(role, FALLBACK_SYSTEM_PROMPT)
    return f"{base} {SHARED_INSTRUCTIONS}"


def _last_user_message(messages: List[Dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                text = " ".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and isinstance(part.get("text"), str)
                ).strip()
                if text:
                    return text
    return ""


def _transcript_prefix(messages: List[Dict[str, Any]]) -> str:
    """Render the earlier conversation turns so Swarms agents keep context."""
    prior = [m for m in messages if m.get("role") in ("user", "assistant")]
    if len(prior) <= 1:
        return ""
    lines: List[str] = []
    for message in prior[:-1]:
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        speaker = "User" if message.get("role") == "user" else "Assistant"
        lines.append(f"{speaker}: {str(content).strip()}")
    return "Conversation so far:\n" + "\n".join(lines) + "\n\n"


def _result_to_text(result: Any) -> str:
    if isinstance(result, str):
        return result.strip()
    if result is None:
        return ""
    if isinstance(result, dict):
        for key in ("content", "output", "result", "text", "final_answer"):
            value = result.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return str(result).strip()
    content = getattr(result, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    return str(result).strip()


def _require_api_key() -> Optional[str]:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return key or None


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "Swarms SEO Office Runtime",
        "runtime": RUNTIME_NAME,
        "vendor": RUNTIME_VENDOR,
        "swarms_version": SWARMS_VERSION,
        "endpoints": ["/health", "/state", "/registry", "/v1/chat/completions"],
        "agents": list(AGENTS.keys()),
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "status": "healthy",
        "runtime": RUNTIME_NAME,
        "swarms_version": SWARMS_VERSION,
        "api_key_configured": bool(_require_api_key()),
    }


@app.get("/state")
async def state() -> Dict[str, Any]:
    default_identity_role = "SEO-Director"
    return {
        "profileName": "swarms-seo-team",
        "registry_profile": "swarms-seo-team",
        "profile": "swarms-seo-team",
        "runtime": {
            "name": RUNTIME_NAME,
            "version": SWARMS_VERSION,
            "vendor": RUNTIME_VENDOR,
            "status": "operational",
            "active_model": DEFAULT_MODEL,
            "governance": "swarms-orchestration",
        },
        "identity": {
            "name": "SEO Director",
            "role": default_identity_role,
            "lane": default_identity_role,
            "model_id": DEFAULT_MODEL,
        },
        # Claw3D turns each key here into an office agent (worker).
        "active": {role: DEFAULT_MODEL for role in AGENTS},
        "agents": [
            {
                "id": role,
                "name": role.replace("-", " "),
                "role": role,
                "model": DEFAULT_MODEL,
                "orchestrator": "swarms",
            }
            for role in AGENTS
        ],
    }


@app.get("/registry")
async def registry() -> Dict[str, Any]:
    return {
        "models": {model: {"provider": "openai", "orchestrator": "swarms"} for model in MODELS},
        "default_model": DEFAULT_MODEL,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON request body.")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object.")

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages must be a non-empty array.")

    role = payload.get("role") if isinstance(payload.get("role"), str) else None
    lane = payload.get("lane") if isinstance(payload.get("lane"), str) else None
    agent_role = _agent_role(role, lane)
    model = payload.get("model") if isinstance(payload.get("model"), str) and payload.get("model").strip() else DEFAULT_MODEL
    task = _last_user_message(messages)
    if not task:
        raise HTTPException(status_code=400, detail="No user message found in messages.")

    api_key = _require_api_key()
    if not api_key:
        return JSONResponse(
            {
                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": (
                                "[swarms-runtime] No OPENAI_API_KEY is configured yet. "
                                "Add OPENAI_API_KEY to this Railway service's variables "
                                "and redeploy — then every SEO team agent will respond "
                                "through Swarms."
                            ),
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        )

    if not SWARMS_AVAILABLE:
        raise HTTPException(status_code=503, detail="swarms library is not available in this container.")

    system_prompt = _system_prompt_for(agent_role)
    full_task = _transcript_prefix(messages) + task

    def _run_agent() -> str:
        agent = Agent(
            agent_name=agent_role,
            agent_description=f"SEO team agent: {agent_role}",
            system_prompt=system_prompt,
            model_name=model,
            max_loops=MAX_LOOPS,
            autosave=False,
            verbose=False,
        )
        return _result_to_text(agent.run(full_task))

    with _RUN_SEMAPHORE:
        loop_start = time.time()
        try:
            text = await _run_agent_async(_run_agent)
        except Exception as error:
            raise HTTPException(status_code=500, detail=f"Swarms agent run failed: {error}")
        elapsed = time.time() - loop_start

    content = text or "[swarms-runtime] The agent returned an empty response."
    return JSONResponse(
        {
            "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "elapsed_seconds": round(elapsed, 2),
            },
        }
    )


async def _run_agent_async(blocking_call):
    """Run the blocking Swarms agent call on a worker thread."""
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, blocking_call)
