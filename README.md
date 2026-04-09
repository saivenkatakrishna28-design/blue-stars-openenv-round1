---
title: Blue Stars Support Triage OpenEnv
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Blue Stars Support Triage OpenEnv

A real-world OpenEnv environment for customer support ticket triage and agent evaluation, developed by **Blue Stars**.

## Overview

Blue Stars Support Triage OpenEnv is designed to evaluate whether an AI agent can make safe, useful, and policy-aware support triage decisions in realistic customer support workflows.

The environment models tasks that support teams actually handle:

- duplicate-charge refund requests
- secure account recovery and verification workflows
- enterprise-grade security incident escalation

This is not a toy or game environment. It is intended to evaluate practical agent behavior under realistic business, safety, and compliance constraints.

## Why this environment is useful

Customer support triage is a high-leverage real-world workflow. A poor triage decision can lead to:

- delayed customer resolution
- improper ticket routing
- mishandled identity verification
- missed security escalation
- privacy or compliance failures

This environment tests whether an agent can distinguish between low-risk, medium-risk, and critical-risk cases while preserving correct routing, urgency, and safety behaviors.

## OpenEnv API

The environment exposes:

- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /health`
- `GET /tasks`

## Task set

### 1. Easy — `easy_refund_request`
A duplicate-charge refund issue with low operational risk but clear billing workflow requirements.

The agent should:
- route to billing
- maintain moderate priority
- use refund/billing tags
- avoid unnecessary escalation

### 2. Medium — `medium_login_locked`
A login and 2FA recovery case that requires identity verification awareness and safe follow-up.

The agent should:
- route to account support
- request further information
- preserve high urgency
- avoid resolving the issue before verification

### 3. Hard — `hard_security_breach`
An enterprise account takeover report involving sensitive information, privilege risk, and urgent escalation requirements.

The agent should:
- route to security or human escalation
- preserve urgent priority
- redact sensitive information
- tag the incident as a security event
- avoid treating the case as a normal account issue

## Difficulty progression

The task suite is intentionally progressive:

- **Easy** tests basic routing and billing correctness
- **Medium** tests verification-aware recovery workflow
- **Hard** tests security reasoning, urgency preservation, redaction, and escalation correctness

This progression makes the environment suitable for comparing weak, moderate, and strong agent policies.

## Observation space

Each observation contains:

- episode metadata
- step index and max steps
- task specification
- ticket details
- workflow stage
- available queues
- available tags
- structured action schema
- contextual metadata

## Action space

The agent action contains:

- `queue`
- `response_type`
- `priority`
- `tags`
- `redact_pii`
- `note`

## Reward design

Reward is deterministic and constrained to `0.0–1.0`.

The reward function combines:

- routing correctness
- response type correctness
- priority correctness
- required tag coverage
- optional tag bonus
- redaction correctness
- workflow correctness
- safety penalties
- compliance penalties
- small efficiency bonus

This produces meaningful partial progress signals rather than only final binary scoring.

## Grader design

Graders are deterministic and rule-based.

They explicitly evaluate:
- whether the case is routed correctly
- whether the selected action type matches task expectations
- whether urgency is preserved
- whether required tags are applied
- whether sensitive information is redacted
- whether escalation happens when mandated
- whether policy rules are violated

This makes scores reproducible and interpretable.

## Multi-step workflow

The environment supports multiple steps per episode:

- analyze
- act
- finalize

This makes the environment more realistic than a single-step classifier and allows the reward function to reflect partial progress and decision quality over time.

## Safety and compliance focus

The hard task is specifically designed to evaluate safety-aware agent behavior.

Unsafe actions are penalized, including:
- missing mandatory escalation
- under-prioritizing urgent incidents
- failing to redact sensitive information
- closing unresolved risky tickets
- treating a security incident like a normal support issue

## Baseline inference

The root `inference.py` script:

- runs all tasks
- uses a reproducible baseline policy
- emits structured logs
- reads model/environment settings from environment variables

## Environment variables

Supported variables include:

- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`
- `OPENAI_API_KEY`
- `SPACE_URL`

## Run locally

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
