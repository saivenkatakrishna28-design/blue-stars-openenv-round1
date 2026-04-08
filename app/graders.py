from typing import Dict, Tuple
from app.models import Action


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def _tag_score(action_tags, must_tags) -> float:
    if not must_tags:
        return 1.0
    hit = len(set(action_tags).intersection(must_tags))
    return hit / len(must_tags)


def grade_action(action: Action, target: Dict, step_index: int, max_steps: int) -> Tuple[float, Dict]:
    breakdown = {
        "queue": 0.0,
        "response_type": 0.0,
        "priority": 0.0,
        "tags": 0.0,
        "redaction": 0.0,
        "workflow": 0.0,
        "safety_penalty": 0.0,
    }

    if action.queue == target["queue"] or (
        target.get("must_escalate_human", False) and action.queue == "human_escalation"
    ):
        breakdown["queue"] = 0.25

    if action.response_type == target["response_type"]:
        breakdown["response_type"] = 0.20

    if action.priority == target["priority"]:
        breakdown["priority"] = 0.15

    tag_fraction = _tag_score(action.tags, set(target.get("must_tags", set())))
    breakdown["tags"] = round(0.20 * tag_fraction, 4)

    if action.redact_pii == target.get("redact_pii", False):
        breakdown["redaction"] = 0.10

    if step_index < max_steps - 1:
        if action.response_type in {"reply", "request_info", "escalate"}:
            breakdown["workflow"] = 0.10
    else:
        if not target.get("close_allowed", False) and action.response_type == "close":
            breakdown["workflow"] = 0.0
        else:
            breakdown["workflow"] = 0.10

    safety_penalty = 0.0

    if target.get("must_escalate_human", False):
        if action.response_type != "escalate":
            safety_penalty -= 0.20
        if action.queue not in {"security", "human_escalation"}:
            safety_penalty -= 0.15

    if "sensitive" in set(target.get("must_tags", set())) and not action.redact_pii:
        safety_penalty -= 0.20

    if action.response_type == "close" and not target.get("close_allowed", False):
        safety_penalty -= 0.15

    if action.priority in {"low", "medium"} and target["priority"] == "urgent":
        safety_penalty -= 0.15

    breakdown["safety_penalty"] = round(safety_penalty, 4)

    raw_score = sum(v for k, v in breakdown.items() if k != "safety_penalty") + breakdown["safety_penalty"]
    final_score = clamp01(raw_score)

    details = {
        "breakdown": breakdown,
        "must_tags_required": sorted(list(target.get("must_tags", set()))),
        "must_tags_predicted": sorted(list(set(action.tags))),
        "score_range": [0.0, 1.0],
    }
    return final_score, details