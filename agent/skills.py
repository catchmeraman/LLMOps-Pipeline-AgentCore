"""
Skills Configuration for LLMOps Agent.
Defines tool schemas, descriptions, categories, and access policies.
Each skill maps to a tool the agent can invoke.
"""

AGENT_SKILLS = {
    "metadata": {
        "agent_name": "llmops-agent",
        "version": "1.0.0",
        "description": "Production DevOps AI Agent with monitoring, remediation, and notification capabilities",
        "model_id": "us.amazon.nova-pro-v1:0",
        "guardrail_id": "<YOUR_GUARDRAIL_ID>",
        "runtime_id": "<YOUR_RUNTIME_ID>"
    },
    "skills": [
        {
            "name": "get_alarms",
            "category": "monitoring",
            "description": "Retrieve CloudWatch alarms filtered by state (ALARM, OK, INSUFFICIENT_DATA, ALL)",
            "parameters": {
                "state": {"type": "string", "enum": ["ALARM", "OK", "INSUFFICIENT_DATA", "ALL"], "default": "ALARM"}
            },
            "returns": {"alarms": "list", "count": "integer"},
            "risk_level": "read_only",
            "cedar_policy": "ALLOW_ALL"
        },
        {
            "name": "get_metric_statistics",
            "category": "monitoring",
            "description": "Get CloudWatch metric statistics for a specific resource over a time window",
            "parameters": {
                "namespace": {"type": "string", "required": True, "example": "AWS/EC2"},
                "metric_name": {"type": "string", "required": True, "example": "CPUUtilization"},
                "dimension_name": {"type": "string", "required": True, "example": "InstanceId"},
                "dimension_value": {"type": "string", "required": True, "example": "i-0abc123"},
                "minutes": {"type": "integer", "default": 30, "min": 5, "max": 1440}
            },
            "returns": {"metric": "string", "datapoints": "list"},
            "risk_level": "read_only",
            "cedar_policy": "ALLOW_ALL"
        },
        {
            "name": "describe_instances",
            "category": "infrastructure",
            "description": "List EC2 instances with their current state, type, and placement",
            "parameters": {
                "status_filter": {"type": "string", "enum": ["all", "running", "stopped"], "default": "all"}
            },
            "returns": {"instances": "list", "count": "integer"},
            "risk_level": "read_only",
            "cedar_policy": "ALLOW_ALL"
        },
        {
            "name": "manage_instance",
            "category": "remediation",
            "description": "Start, stop, or reboot an EC2 instance",
            "parameters": {
                "instance_id": {"type": "string", "required": True, "pattern": "^i-[a-f0-9]+$"},
                "action": {"type": "string", "enum": ["start", "stop", "reboot"], "required": True}
            },
            "returns": {"instance_id": "string", "action": "string", "status": "string"},
            "risk_level": "destructive",
            "cedar_policy": "ALLOW_SENIOR_ONLY",
            "requires_confirmation": True
        },
        {
            "name": "run_command",
            "category": "remediation",
            "description": "Execute a shell command on an EC2 instance via SSM Run Command",
            "parameters": {
                "instance_id": {"type": "string", "required": True},
                "command": {"type": "string", "required": True, "max_length": 500}
            },
            "returns": {"status": "string", "output": "string", "error": "string"},
            "risk_level": "destructive",
            "cedar_policy": "ALLOW_SENIOR_ONLY",
            "blocked_patterns": ["rm -rf", "mkfs", "dd if=", "shutdown", "> /dev/"]
        },
        {
            "name": "send_notification",
            "category": "notification",
            "description": "Send a notification to the operations team via SNS",
            "parameters": {
                "subject": {"type": "string", "required": True, "max_length": 100},
                "message": {"type": "string", "required": True, "max_length": 2000}
            },
            "returns": {"message_id": "string", "status": "string"},
            "risk_level": "low",
            "cedar_policy": "ALLOW_ALL"
        }
    ],
    "skill_categories": {
        "monitoring": {"description": "Read-only observability tools", "risk": "none"},
        "infrastructure": {"description": "Resource discovery and listing", "risk": "none"},
        "remediation": {"description": "Actions that modify infrastructure", "risk": "high"},
        "notification": {"description": "Communication and alerting", "risk": "low"}
    },
    "cedar_policies": {
        "ALLOW_ALL": "permit(principal, action == Action::\"InvokeTool\", resource);",
        "ALLOW_SENIOR_ONLY": "permit(principal, action == Action::\"InvokeTool\", resource) when { principal.role == \"senior_engineer\" };",
        "DENY_DESTRUCTIVE": "forbid(principal, action == Action::\"InvokeTool\", resource) when { resource.toolName in [\"manage_instance\", \"run_command\"] && principal.role == \"viewer\" };"
    }
}


def get_skill_summary() -> str:
    """Return a formatted summary of all agent skills for display."""
    lines = [f"Agent: {AGENT_SKILLS['metadata']['agent_name']} v{AGENT_SKILLS['metadata']['version']}",
             f"Model: {AGENT_SKILLS['metadata']['model_id']}",
             f"Guardrail: {AGENT_SKILLS['metadata']['guardrail_id']}",
             f"Runtime: {AGENT_SKILLS['metadata']['runtime_id']}",
             "", "Skills:"]
    for skill in AGENT_SKILLS["skills"]:
        risk_icon = {"read_only": "🟢", "low": "🟡", "destructive": "🔴"}[skill["risk_level"]]
        lines.append(f"  {risk_icon} {skill['name']} [{skill['category']}] — {skill['description']}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_skill_summary())
