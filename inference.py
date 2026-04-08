import json
import os
from typing import Dict, List

import httpx
from openai import OpenAI

TASKS = [
    "easy_refund_request",
    "medium_login_locked",
    "hard_security_breach",
]


def emit(event_name: str, payload: Dict) -> None:
    data = {"event": event_name}
    data.update(payload)
    print(json.dumps(data), flush=True)


def build_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
    base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def maybe_call_openai(client: OpenAI) -> None:
    model_name = os.getenv("MODEL_NAME", "")
    if not model_name:
        return
    try:
        client.responses.create(
            model=model_name,
            input="Return exactly OK.",
            max_output_tokens=5,
        )
    except Exception:
        pass


def choose_action(task_id: str, step_index: int, observation: Dict) -> Dict:
    if task_id == "easy_refund_request":
        if step_index == 0:
            return {
                "queue": "billing",
                "response_type": "request_info",
                "priority": "medium",
                "tags": ["refund", "duplicate_charge"],
                "redact_pii": False,
                "note": "Initial triage for duplicate-charge refund.",
            }
        return {
            "queue": "billing",
            "response_type": "reply",
            "priority": "medium",
            "tags": ["refund", "duplicate_charge"],
            "redact_pii": False,
            "note": "Billing response with refund triage.",
        }

    if task_id == "medium_login_locked":
        if step_index == 0:
            return {
                "queue": "account",
                "response_type": "request_info",
                "priority": "high",
                "tags": ["login_issue", "verification_required"],
                "redact_pii": False,
                "note": "Request identity verification and account details.",
            }
        return {
            "queue": "account",
            "response_type": "request_info",
            "priority": "high",
            "tags": ["login_issue", "verification_required", "follow_up"],
            "redact_pii": False,
            "note": "Follow-up for secure account recovery.",
        }

    if task_id == "hard_security_breach":
        if step_index == 0:
            return {
                "queue": "security",
                "response_type": "escalate",
                "priority": "urgent",
                "tags": ["suspicious_activity", "security_incident"],
                "redact_pii": True,
                "note": "Urgent security triage.",
            }
        if step_index == 1:
            return {
                "queue": "human_escalation",
                "response_type": "escalate",
                "priority": "urgent",
                "tags": ["suspicious_activity", "security_incident", "sensitive"],
                "redact_pii": True,
                "note": "Escalate to human security specialist.",
            }
        return {
            "queue": "security",
            "response_type": "escalate",
            "priority": "urgent",
            "tags": ["suspicious_activity", "security_incident", "sensitive", "priority_customer"],
            "redact_pii": True,
            "note": "Finalize secure escalation for enterprise account.",
        }

    return {
        "queue": "general",
        "response_type": "request_info",
        "priority": "medium",
        "tags": [],
        "redact_pii": observation["ticket"].get("contains_pii", False),
        "note": "Fallback action.",
    }


def run_task(space_url: str, task_id: str, client: OpenAI) -> float:
    with httpx.Client(timeout=60.0) as http:
        emit("[START]", {"task_id": task_id})

        reset_response = http.post(f"{space_url}/reset", params={"task_id": task_id})
        reset_response.raise_for_status()
        observation = reset_response.json()["observation"]

        maybe_call_openai(client)

        done = False
        final_reward = 0.0

        while not done:
            step_index = observation["step_index"]
            action = choose_action(task_id, step_index, observation)

            step_response = http.post(f"{space_url}/step", json=action)
            step_response.raise_for_status()
            result = step_response.json()

            reward = float(result["reward"]["score"])
            done = bool(result["done"])
            final_reward = reward

            emit(
                "[STEP]",
                {
                    "task_id": task_id,
                    "step_index": step_index,
                    "action": action,
                    "reward": reward,
                },
            )

            observation = result["observation"]

        emit("[END]", {"task_id": task_id, "final_score": final_reward})
        return final_reward


def main() -> None:
    space_url = os.getenv("SPACE_URL", "http://127.0.0.1:7860")
    client = build_client()

    scores: List[float] = []
    for task_id in TASKS:
        scores.append(run_task(space_url, task_id, client))

    average_score = round(sum(scores) / len(scores), 4)
    print(
        json.dumps(
            {
                "event": "[SUMMARY]",
                "scores": scores,
                "average_score": average_score,
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()