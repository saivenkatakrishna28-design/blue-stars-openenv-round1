from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


Difficulty = Literal["easy", "medium", "hard"]
CustomerTier = Literal["free", "pro", "enterprise"]
Category = Literal["billing", "technical", "account", "shipping", "refund", "security"]
Priority = Literal["low", "medium", "high", "urgent"]
Sentiment = Literal["calm", "frustrated", "angry"]
QueueName = Literal["general", "billing", "tech", "account", "security", "human_escalation"]
ResponseType = Literal["reply", "request_info", "escalate", "close"]


class Ticket(BaseModel):
    ticket_id: str
    customer_tier: CustomerTier
    category: Category
    priority: Priority
    sentiment: Sentiment
    requires_human: bool
    contains_pii: bool
    summary: str


class TaskSpec(BaseModel):
    task_id: str
    difficulty: Difficulty
    objective: str
    expected_steps: int
    allowed_actions: List[str]


class Observation(BaseModel):
    episode_id: str
    task_id: str
    step_index: int
    max_steps: int
    task: TaskSpec
    ticket: Ticket
    workflow_stage: Literal["analyze", "act", "finalize"]
    instructions: str
    available_queues: List[str]
    available_tags: List[str]
    action_schema: Dict[str, Any]
    context: Dict[str, Any]


class Action(BaseModel):
    queue: QueueName
    response_type: ResponseType
    priority: Priority
    tags: List[str] = Field(default_factory=list)
    redact_pii: bool = False
    note: str = ""


class Reward(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    reason: str
    breakdown: Dict[str, float] = Field(default_factory=dict)


class State(BaseModel):
    episode_id: str
    task_id: str
    difficulty: Difficulty
    step_index: int
    max_steps: int
    done: bool
    workflow_stage: str
    cumulative_reward: float
    history: List[Dict[str, Any]]
    hidden_target: Dict[str, Any]
    ticket: Ticket


class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]


class ResetResponse(BaseModel):
    observation: Observation


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str