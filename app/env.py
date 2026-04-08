from typing import Dict, Optional
from app.models import Action, Reward, State, StepResult, ResetResponse
from app.tasks import get_task_bundle, list_task_ids
from app.utils import build_observation, make_episode_id, normalize_tags
from app.graders import grade_action


class SupportTriageEnv:
    def __init__(self) -> None:
        self.current_state: Optional[Dict] = None
        self.default_task_id = list_task_ids()[0]

    def reset(self, task_id: Optional[str] = None) -> ResetResponse:
        selected_task_id = task_id or self.default_task_id
        bundle = get_task_bundle(selected_task_id)

        self.current_state = {
            "episode_id": make_episode_id(),
            "task_id": bundle["task"].task_id,
            "task": bundle["task"],
            "difficulty": bundle["task"].difficulty,
            "step_index": 0,
            "max_steps": bundle["task"].expected_steps,
            "done": False,
            "workflow_stage": "analyze",
            "cumulative_reward": 0.0,
            "history": [],
            "hidden_target": bundle["target"],
            "ticket": bundle["ticket"],
        }
        return ResetResponse(observation=build_observation(self.current_state))

    def state(self) -> State:
        if self.current_state is None:
            raise ValueError("Environment not initialized. Call reset() first.")
        return State(
            episode_id=self.current_state["episode_id"],
            task_id=self.current_state["task_id"],
            difficulty=self.current_state["difficulty"],
            step_index=self.current_state["step_index"],
            max_steps=self.current_state["max_steps"],
            done=self.current_state["done"],
            workflow_stage=self.current_state["workflow_stage"],
            cumulative_reward=round(self.current_state["cumulative_reward"], 4),
            history=self.current_state["history"],
            hidden_target=self.current_state["hidden_target"],
            ticket=self.current_state["ticket"],
        )

    def step(self, action: Action) -> StepResult:
        if self.current_state is None:
            raise ValueError("Environment not initialized. Call reset() first.")
        if self.current_state["done"]:
            raise ValueError("Episode already finished. Call reset() again.")

        clean_action = Action(
            queue=action.queue,
            response_type=action.response_type,
            priority=action.priority,
            tags=normalize_tags(action.tags),
            redact_pii=action.redact_pii,
            note=action.note.strip(),
        )

        score, details = grade_action(
            clean_action,
            self.current_state["hidden_target"],
            self.current_state["step_index"],
            self.current_state["max_steps"],
        )

        self.current_state["history"].append(
            {
                "step_index": self.current_state["step_index"],
                "action": clean_action.model_dump(),
                "score": score,
                "details": details,
            }
        )

        self.current_state["cumulative_reward"] += score
        self.current_state["step_index"] += 1
        self.current_state["workflow_stage"] = (
            "finalize" if self.current_state["step_index"] >= self.current_state["max_steps"] - 1 else "act"
        )

        if self.current_state["step_index"] >= self.current_state["max_steps"]:
            self.current_state["done"] = True

        reward = Reward(
            score=score,
            reason="Deterministic grading across routing, priority, tags, safety, and workflow correctness.",
            breakdown=details["breakdown"],
        )

        observation = build_observation(self.current_state)
        info = {
            "task_id": self.current_state["task_id"],
            "difficulty": self.current_state["difficulty"],
            "grader_details": details,
            "history_length": len(self.current_state["history"]),
            "valid_score_range": [0.0, 1.0],
        }

        return StepResult(
            observation=observation,
            reward=reward,
            done=self.current_state["done"],
            info=info,
        )