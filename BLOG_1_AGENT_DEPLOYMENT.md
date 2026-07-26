# 🏗️ Building a Production AI Agent on Amazon Bedrock AgentCore — From Code to Deployment

> Part 1 of 3: How I deployed a DevOps AI agent with tools, guardrails, and CI/CD — hitting (and fixing) every error along the way.

**Author:** Ramandeep Chandna | **Date:** July 2026 | **Level:** 300+
**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore
**Series:** LLMOps Pipeline on AWS — Building, Evaluating, and Optimizing AI Agents

---

## 📖 Series Navigation

| Part | Blog | Status |
|------|------|--------|
| **Prequel** | [How I Built an IT Operations Agent on AgentCore](https://github.com/catchmeraman/it-ops-agent-complete) | ✅ Deployed |
| **→ Part 1** | **This blog** — Building a Production Agent with LLMOps practices | You are here |
| Part 2 | [Getting Managed Evaluation Working on Container Runtimes](./BLOG_2_EVALUATION.md) | Next |
| Part 3 | [Running a Production AI Agent for $3.35/Month](./BLOG_3_COST_OPTIMIZATION.md) | Final |

---

## 🔗 Where We Left Off (From the IT Ops Agent Blog)

In my [previous blog](https://github.com/catchmeraman/it-ops-agent-complete), I built and deployed an IT Operations Agent on AgentCore Runtime with:
- ✅ 12 tools (CloudWatch, EC2, SSM, SNS, CloudTrail, Knowledge Base)
- ✅ CI/CD pipeline (CodeCommit → CodeBuild → ECR → AgentCore)
- ✅ Production deployment (Runtime v8, all tests passing)

**What was MISSING from that deployment:**
- ❌ No evaluation — how do we know the agent's answers are good?
- ❌ No guardrails — what stops prompt injection or PII leaks?
- ❌ No observability traces — can't see what the agent did step-by-step
- ❌ No cost optimization — using Claude Sonnet ($3/1M tokens) without considering alternatives
- ❌ No memory — agent forgets everything between sessions

**This blog series adds all of that.** We take the same agent pattern and build a complete LLMOps pipeline around it.

---

## How This Blog Differs from the IT Ops Agent Blog

| Aspect | IT Ops Agent Blog | This Blog (LLMOps Pipeline) |
|--------|-------------------|----------------------------|
| **Focus** | Build & deploy an agent | Operate, evaluate, and optimize an agent |
| **Model** | Claude Sonnet 4 | Amazon Nova Pro (78% cheaper) |
| **Evaluation** | None | 9 evaluators (LLM-as-Judge) |
| **Guardrails** | None | Content + PII + Prompt Injection |
| **Observability** | Basic CloudWatch logs | OpenTelemetry traces with session.id |
| **Memory** | None | DynamoDB cross-session persistence |
| **Cost** | ~$15/month | $3.35/month (optimized) |
| **CI/CD** | Deploy only | Deploy + Evaluate + Quality Gate |

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

## 📁 Code Reference (All in GitHub Repo)

| File | What It Does |
|------|-------------|
| [`agent/main.py`](./agent/main.py) | HTTP server with OTEL session baggage |
| [`agent/agent.py`](./agent/agent.py) | Strands Agent + Nova Pro + 6 tools |
| [`agent/tools/`](./agent/tools/) | CloudWatch, EC2, SSM, SNS tool implementations |
| [`agent/skills.py`](./agent/skills.py) | Tool schemas, risk levels, Cedar policies |
| [`agent/memory.py`](./agent/memory.py) | DynamoDB cross-session persistence |
| [`agent/observability.py`](./agent/observability.py) | CloudWatch custom metrics + dashboard |
| [`Dockerfile`](./Dockerfile) | ARM64 container with OTEL auto-instrumentation |
| [`buildspec.yml`](./buildspec.yml) | CodeBuild CI/CD instructions |
| [`requirements.txt`](./requirements.txt) | Dependencies (strands + ADOT SDK) |

---

## What's Next: The Agent Works — But Is It Any Good?

We have a deployed, working agent. But how do we know:
- Are the answers correct?
- Is it safe?
- Does it pick the right tools?
- Is it getting better or worse over time?

**→ [Part 2: Getting Managed Evaluation Working on Container Runtimes](./BLOG_2_EVALUATION.md)**

In Part 2, I configure 9 evaluators (5 built-in + 4 custom with Nova Pro as judge) and discover that getting evaluation to work on container runtimes requires solving 7 challenges — including one undocumented fix (`session.id` baggage) that took an entire night to find.

---

**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore
