# 🏗️ Building a Production AI Agent on Amazon Bedrock AgentCore — From Code to Deployment

> How I deployed a DevOps AI agent with tools, guardrails, and CI/CD — hitting (and fixing) every error along the way.

**Author:** Ramandeep Chandna | **Date:** July 2026 | **Level:** 300+
**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore

---

## What We Built

A production-ready **DevOps AI Agent** that monitors, diagnoses, and remediates AWS infrastructure — deployed on Amazon Bedrock AgentCore Runtime with full CI/CD automation.

**Stack:**
- Agent Framework: Strands Agents + Amazon Nova Pro
- Runtime: AgentCore (serverless container, ARM64)
- Security: Bedrock Guardrails (content + PII + prompt injection defense)
- CI/CD: CodeBuild (ARM64) → ECR → AgentCore auto-deploy
- Observability: OpenTelemetry + CloudWatch

---

## Architecture

![Complete Architecture](generated-diagrams/01_complete_architecture.png)

![CI/CD Pipeline](generated-diagrams/02_cicd_pipeline.png)

![Security - 5 Layer Guardrails](generated-diagrams/04_security_guardrails.png)

---

## The Agent

**6 tools, 1 model, 1 system prompt:**

```python
from strands import Agent
from strands.models import BedrockModel

MODEL_ID = "us.amazon.nova-pro-v1:0"  # AWS credits covered

agent = Agent(
    model=BedrockModel(model_id=MODEL_ID, region_name="us-east-1"),
    system_prompt="You are a production DevOps AI Agent...",
    tools=[get_alarms, get_metric_statistics, describe_instances, 
           manage_instance, run_command, send_notification]
)
```

**Guardrail Configuration:**
- Content filter: PROMPT_ATTACK=HIGH, Violence/Hate/Sexual=HIGH
- PII: SSN/Credit Card=BLOCK, Email/Phone=ANONYMIZE
- Topics: Credential exposure=DENY, Destructive operations=DENY

---

## Deployment: The Dockerfile

```dockerfile
FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/main.py agent/agent.py ./
COPY agent/tools/ ./tools/
EXPOSE 8080
CMD ["opentelemetry-instrument", "python", "main.py"]
```

**Key:** AgentCore requires ARM64. Use `opentelemetry-instrument` for auto-tracing.

---

## CI/CD Pipeline

```yaml
# buildspec.yml - CodeBuild ARM64
phases:
  pre_build:
    commands:
      - aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
  build:
    commands:
      - docker build -t $ECR_REPO:$IMAGE_TAG .
      - docker push $ECR_URI/$ECR_REPO:$IMAGE_TAG
  post_build:
    commands:
      - printf '{"agentRuntimeId":"%s",...}' > /tmp/update.json
      - aws bedrock-agentcore-control update-agent-runtime --cli-input-json file:///tmp/update.json
```

**Flow:** `git push` → EventBridge → CodePipeline → CodeBuild (ARM64) → ECR → AgentCore update → READY

---

## Challenges & Solutions

| # | Error | Fix |
|---|-------|-----|
| 1 | `exit code 252` — wrong CLI | Use `bedrock-agentcore-control` (control plane) |
| 2 | `Architecture incompatible: arm64` | Switch CodeBuild to `ARM_CONTAINER` |
| 3 | `429 Too Many Requests` Docker Hub | Use `public.ecr.aws/docker/library/python:3.13-slim` |
| 4 | `AccessDeniedException: iam:PassRole` | Add PassRole to CodeBuild role |
| 5 | `Model marked as Legacy` | Use inference profile: `us.amazon.nova-pro-v1:0` |
| 6 | Marketplace 403 on Claude | Switch to Amazon Nova Pro (credits covered) |

---

## Cost

| Component | Monthly Cost |
|-----------|-------------|
| AgentCore Runtime | $0.71 (only when invoked) |
| Nova Pro tokens | $0.38 |
| CodeBuild (ARM64) | ~$5 |
| Guardrails | $0.01 |
| ECR storage | $0.10 |
| **Total** | **~$6-10/month** |

---

## 📸 Screenshots to Capture

| # | What | Console Path |
|---|------|-------------|
| 1 | Runtime READY v11 | Bedrock → AgentCore → Runtimes |
| 2 | Runtime config (container URI, env vars) | Click runtime → Configuration |
| 3 | Version history (v1→v11) | Runtime → Versions |
| 4 | Guardrail config | Bedrock → Guardrails |
| 5 | Guardrail TEST — prompt injection BLOCKED | Guardrails → Test tab |
| 6 | CodeBuild history (9+ green) | CodeBuild → llmops-agent-build |
| 7 | ECR images | ECR → bedrock-agentcore-llmops-agent |
| 8 | CloudWatch runtime logs | CloudWatch → Log groups → llmops_agent |
| 9 | IAM role permissions | IAM → event-agent-role |

---

## Key Takeaways

1. **ARM64 from day one** — AgentCore requires it, save yourself failed builds
2. **`bedrock-agentcore-control`** for management, `bedrock-agentcore` for invocations
3. **Nova Pro** — best price/performance for agents, covered by AWS credits
4. **Guardrails are non-negotiable** — prompt injection defense must be ON in production
5. **`--cli-input-json file://`** — never fight shell escaping for complex JSON

---

*Next in series: [Part 2: Getting Managed Evaluation Working on Container Runtimes](./BLOG_2_EVALUATION.md)*

**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore
