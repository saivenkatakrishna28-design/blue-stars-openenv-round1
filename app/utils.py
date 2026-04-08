import uuid
from typing import Dict, List
from app.models import Observation
from app.tasks import AVAILABLE_QUEUES, AVAILABLE_TAGS


def make_episode_id() -> str:
    return str(uuid.uuid4())


def build_action_schema() -> Dict:
    return {
        "type": "object",
        "properties": {
            "queue": {
                "type": "string",
                "enum": AVAILABLE_QUEUES,
            },
            "response_type": {
                "type": "string",
                "enum": ["reply", "request_info", "escalate", "close"],
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
            },
            "redact_pii": {"type": "boolean"},
            "note": {"type": "string"},
        },
        "required": ["queue", "response_type", "priority"],
    }


def stage_name(step_index: int, max_steps: int) -> str:
    if step_index == 0:
        return "analyze"
    if step_index >= max_steps - 1:
        return "finalize"
    return "act"


def build_context(state: Dict) -> Dict:
    return {
        "customer_tier": state["ticket"].customer_tier,
        "ticket_category": state["ticket"].category,
        "requires_human": state["ticket"].requires_human,
        "contains_pii": state["ticket"].contains_pii,
        "history_length": len(state["history"]),
        "expected_steps": state["task"].expected_steps,
    }


def build_observation(state: Dict) -> Observation:
    instructions = (
        "You are an AI customer support triage agent. "
        "Make safe, deterministic, high-utility triage decisions. "
        "Choose the correct queue, response_type, priority, tags, and redaction flag. "
        "Avoid unsafe closure, missed escalation, and mishandling of sensitive information."
    )
    workflow_stage = stage_name(state["step_index"], state["max_steps"])
    return Observation(
        episode_id=state["episode_id"],
        task_id=state["task_id"],
        step_index=state["step_index"],
        max_steps=state["max_steps"],
        task=state["task"],
        ticket=state["ticket"],
        workflow_stage=workflow_stage,
        instructions=instructions,
        available_queues=AVAILABLE_QUEUES,
        available_tags=AVAILABLE_TAGS,
        action_schema=build_action_schema(),
        context=build_context(state),
    )


def normalize_tags(tags: List[str]) -> List[str]:
    unique = []
    seen = set()
    for tag in tags:
        if isinstance(tag, str):
            cleaned = tag.strip()
            if cleaned and cleaned not in seen:
                unique.append(cleaned)
                seen.add(cleaned)
    return unique