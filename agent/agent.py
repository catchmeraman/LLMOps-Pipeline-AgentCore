"""LLMOps Agent — Agent definition with Strands + Claude Sonnet 4."""
import os
from strands import Agent
from strands.models import BedrockModel
from tools.cloudwatch_tools import get_alarms, get_metric_statistics
from tools.ec2_tools import describe_instances, manage_instance
from tools.ssm_tools import run_command
from tools.sns_tools import send_notification

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

SYSTEM_PROMPT = """You are a production DevOps AI Agent managing AWS infrastructure.

## Capabilities:
1. MONITOR: CloudWatch alarms and metrics
2. MANAGE: EC2 instances (start/stop/reboot)
3. EXECUTE: Remote commands via SSM
4. NOTIFY: Send alerts via SNS

## Operating Rules:
- ALWAYS diagnose before taking action
- NEVER execute destructive commands without explaining why first
- Provide clear summaries of findings and actions taken
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
