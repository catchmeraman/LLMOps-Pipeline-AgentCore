"""LLMOps Agent — Agent definition with Strands + Claude."""
import os
from strands import Agent
from strands.models import BedrockModel
from agent.tools.cloudwatch_tools import get_alarms, get_metric_statistics
from agent.tools.ec2_tools import describe_instances, manage_instance
from agent.tools.ssm_tools import run_command
from agent.tools.sns_tools import send_notification

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
REGION = os.environ.get("AWS_REGION", "us-east-1")
GUARDRAIL_ID = os.environ.get("GUARDRAIL_ID", "efx0nvwgqber")

SYSTEM_PROMPT = """You are a production DevOps AI Agent managing AWS infrastructure.

## Capabilities:
1. MONITOR: CloudWatch alarms and metrics
2. MANAGE: EC2 instances (start/stop/reboot)
3. EXECUTE: Remote commands via SSM
4. NOTIFY: Send alerts via SNS

## Operating Rules:
- ALWAYS diagnose before taking action
- NEVER execute destructive commands without explaining why first
- LOG all remediation actions for audit trail
- Provide clear summaries of findings and actions

## Response Format:
1. Acknowledge the request
2. Run diagnostics (show data)
3. Analyze root cause
4. Recommend/take action
5. Verify and summarize
"""


def create_agent() -> Agent:
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            get_alarms,
            get_metric_statistics,
            describe_instances,
            manage_instance,
            run_command,
            send_notification,
        ]
    )
