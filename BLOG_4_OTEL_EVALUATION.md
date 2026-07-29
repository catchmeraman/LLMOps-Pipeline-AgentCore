# 📡 OpenTelemetry + Managed Evaluation for Container Runtimes — Complete Setup Guide

> Part 4: How to configure OTEL traces on AgentCore Container Runtimes so Managed Evaluation can find and score your sessions.

**Author:** Ramandeep Chandna | **Date:** July 2026 | **Level:** 300+
**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore
**Series:** LLMOps Pipeline on AWS — Building, Evaluating, and Optimizing AI Agents

---

## 📖 Series Navigation

| Part | Blog | Status |
|------|------|--------|
| Prequel | [How I Built a Production LLMOps Pipeline on AWS AgentCore End to End](https://github.com/catchmeraman/it-ops-agent-complete) | Foundation |
| Part 1 | [Building a Production Agent](./BLOG_1_AGENT_DEPLOYMENT.md) | Agent deployed ✅ |
| Part 2 | [Getting Evaluation Working](./BLOG_2_EVALUATION.md) | 9 evaluators ✅ |
| Part 3 | [Cost-Optimized LLMOps for $3.35/Month](./BLOG_3_COST_OPTIMIZATION.md) | Optimized ✅ |
| **→ Part 4** | **This blog** — OTEL + Evaluation for Container Runtimes | You are here |

---

## The Problem

You deploy an agent on AgentCore Container Runtime. It works great. You want to run Managed Evaluation to score session quality. You configure evaluators. Result:

```
"0 sessions tested successfully."
```

**Why?** Because evaluation relies on **OpenTelemetry traces** to find sessions. If OTEL isn't configured correctly, your agent runs fine but is **invisible to the evaluation system**.

This blog documents the exact setup required — every env var, every package, every gotcha — validated on our LLMOps Pipeline Agent (v14 → v28, 17 errors fixed along the way).

---

## How Evaluation Finds Your Sessions

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Agent Container    │────▶│  CloudWatch Logs      │────▶│  Evaluation API │
│  (opentelemetry-    │     │  otel-rt-logs stream  │     │  (downloads     │
│   instrument)       │     │  + aws/spans          │     │   spans, scores)│
└─────────────────────┘     └──────────────────────┘     └─────────────────┘
```

1. `opentelemetry-instrument` wraps your Python process
2. ADOT SDK auto-instruments all boto3/HTTP calls as spans
3. Spans are exported via OTLP to CloudWatch (`otel-rt-logs` stream)
4. Evaluation API queries CloudWatch for spans with matching `session.id`
5. Spans are scored by built-in or custom evaluators

**If step 1 is missing → steps 2-5 never happen → "0 sessions tested"**

---

## Complete Configuration (11 Requirements)

### 1. Dockerfile — The Critical CMD

```dockerfile
FROM public.ecr.aws/docker/library/python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./
COPY agent/tools/ ./tools/

EXPOSE 8080

# ⚠️ THIS IS THE KEY — opentelemetry-instrument auto-exports spans
CMD ["opentelemetry-instrument", "python", "main.py"]
```

**Common mistake:** Using `CMD ["python", "main.py"]` — agent works but NO traces are exported.

### 2. requirements.txt

```
strands-agents>=0.1.0
bedrock-agentcore>=1.0.0
aws-opentelemetry-distro>=0.10.0    # ← Provides xray propagator + ADOT
boto3>=1.35.0
```

**Why `aws-opentelemetry-distro`?** It provides:
- The `xray` propagator (required by `OTEL_PROPAGATORS` env var)
- AWS-specific OTEL configuration (`aws_distro`, `aws_configurator`)
- Auto-instrumentation for boto3, HTTP, and other libraries

Without it: `ValueError: Propagator xray not found`

### 3. Environment Variables (set on AgentCore Runtime)

```bash
AGENT_OBSERVABILITY_ENABLED=true
OTEL_PROPAGATORS=baggage,xray,tracecontext
OTEL_PYTHON_DISTRO=aws_distro
OTEL_PYTHON_CONFIGURATOR=aws_configurator
OTEL_TRACES_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_RESOURCE_ATTRIBUTES=service.name=your_agent_name
```

All 7 are required. Missing any one can cause silent failures.

### 4. Agent Code — BedrockAgentCoreApp with session.id

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from opentelemetry import baggage, context

app = BedrockAgentCoreApp()

@app.entrypoint
def runtime_handler(payload, context_obj):
    data = json.loads(payload)
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    # Set session.id baggage for OTEL correlation
    ctx = baggage.set_baggage("session.id", session_id)
    token = context.attach(ctx)
    
    try:
        # Your agent logic here
        result = handle_request(data["prompt"], ...)
        return json.dumps(result)
    finally:
        context.detach(token)

app.run()
```

**Note:** AgentCore Runtime handles `runtimeSessionId` → `session.id` automatically. The manual baggage is for additional custom attributes.

---

## Verification — Is OTEL Working?

### Check 1: CloudWatch Log Stream Exists

```
Console: CloudWatch → Log groups →
  /aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT
  
Look for stream: otel-rt-logs
```

### Check 2: Recent Events in Stream

```bash
aws logs get-log-events \
  --log-group-name /aws/bedrock-agentcore/runtimes/<YOUR_RUNTIME_ID>-DEFAULT \
  --log-stream-name otel-rt-logs \
  --limit 5
```

### Check 3: Span Content Shows Your Service

```json
{
  "resource": {
    "attributes": {
      "service.name": "llmops_agent",
      "telemetry.sdk.name": "opentelemetry",
      "telemetry.sdk.version": "1.44.0",
      "telemetry.auto.version": "0.19.0-aws"
    }
  },
  "scopeSpans": [...]
}
```

### Check 4: Query Spans by Session

```sql
fields @timestamp, @message
| filter ispresent(scope.name) and ispresent(attributes.session.id)
| filter attributes.session.id = "your-session-id"
| sort @timestamp asc
```

---

## Running Evaluation

### Option 1: AgentCore CLI (Easiest)

```bash
# Install
npm install -g @aws/agentcore

# Run evaluation on a session
agentcore run eval \
  --runtime llmops_agent \
  --session-id "eval-ready-session-otel-test-20260729-2240" \
  --evaluator "Builtin.Helpfulness" \
  --evaluator "Builtin.ToolSelectionAccuracy"
```

### Option 2: Python SDK

```python
from bedrock_agentcore_starter_toolkit import Evaluation

eval_client = Evaluation()
results = eval_client.run(
    agent_id="<YOUR_RUNTIME_ID>",
    session_id="your-session-id",
    evaluators=["Builtin.Helpfulness", "Builtin.ToolSelectionAccuracy"]
)

for r in results.get_successful_results():
    print(f"  {r.evaluator_name}: {r.value:.2f} - {r.label}")
```

### Option 3: AWS SDK (Download spans → Evaluate)

```python
import boto3, json, time
from datetime import datetime, timedelta

region = "us-east-1"
agent_id = "<YOUR_RUNTIME_ID>"
session_id = "your-session-id"

# Step 1: Download spans from CloudWatch
logs_client = boto3.client('logs', region_name=region)

query = f"""fields @timestamp, @message
| filter ispresent(scope.name) and ispresent(attributes.session.id)
| filter attributes.session.id = "{session_id}"
| sort @timestamp asc"""

query_id = logs_client.start_query(
    logGroupName=f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT",
    startTime=int((datetime.now() - timedelta(hours=1)).timestamp()),
    endTime=int(datetime.now().timestamp()),
    queryString=query
)['queryId']

# Wait for results
while True:
    result = logs_client.get_query_results(queryId=query_id)
    if result['status'] in ['Complete', 'Failed']:
        break
    time.sleep(1)

# Extract span JSON
session_spans = [json.loads(f['value']) for row in result['results']
                 for f in row if f['field'] == '@message' and f['value'].startswith('{')]

# Step 2: Call Evaluate API
ace_client = boto3.client('bedrock-agentcore', region_name=region)
response = ace_client.evaluate(
    evaluatorId="Builtin.Helpfulness",
    evaluationInput={"sessionSpans": session_spans}
)

print(response["evaluationResults"])
```

---

## 13 Built-in Evaluators Available

| Evaluator | Level | Needs Ground Truth | Scores |
|-----------|-------|-------------------|--------|
| `Builtin.Correctness` | TRACE | `expected_response` | Factual accuracy |
| `Builtin.Faithfulness` | TRACE | None | Supported by context |
| `Builtin.Helpfulness` | TRACE | None | Usefulness |
| `Builtin.ResponseRelevance` | TRACE | None | Addresses query |
| `Builtin.Conciseness` | TRACE | None | Brief without loss |
| `Builtin.Coherence` | TRACE | None | Logically structured |
| `Builtin.InstructionFollowing` | TRACE | None | Follows system prompt |
| `Builtin.Refusal` | TRACE | None | Detects evasion |
| `Builtin.Harmfulness` | TRACE | None | Harmful content |
| `Builtin.Stereotyping` | TRACE | None | Group generalizations |
| `Builtin.GoalSuccessRate` | SESSION | `assertions` | Meets user goals |
| `Builtin.ToolSelectionAccuracy` | SESSION | None | Correct tool chosen |
| `Builtin.ToolParameterAccuracy` | SESSION | None | Accurate parameters |

**TRACE** = one score per turn. **SESSION** = one score per conversation.

---

## 3 Evaluation Interfaces

| Interface | Best For | How |
|-----------|----------|-----|
| `EvaluationClient` | Ad-hoc debugging, CI spot-checks | Synchronous, per session |
| `OnDemandEvaluationDatasetRunner` | Regression testing, CI/CD pipelines | Runs agent + evaluates per scenario |
| `BatchEvaluationRunner` | Baseline snapshots, large-scale | Service-side, aggregate scores |

---

## Our Agent's Configuration (Verified v28)

| Requirement | Value | Status |
|-------------|-------|--------|
| Dockerfile CMD | `opentelemetry-instrument python main.py` | ✅ |
| `aws-opentelemetry-distro` | `>=0.10.0` in requirements.txt | ✅ |
| `bedrock-agentcore` | `>=1.0.0` in requirements.txt | ✅ |
| `AGENT_OBSERVABILITY_ENABLED` | `true` | ✅ |
| `OTEL_PROPAGATORS` | `baggage,xray,tracecontext` | ✅ |
| `OTEL_PYTHON_DISTRO` | `aws_distro` | ✅ |
| `OTEL_PYTHON_CONFIGURATOR` | `aws_configurator` | ✅ |
| `OTEL_TRACES_EXPORTER` | `otlp` | ✅ |
| `OTEL_LOGS_EXPORTER` | `otlp` | ✅ |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | ✅ |
| `OTEL_RESOURCE_ATTRIBUTES` | `service.name=llmops_agent` | ✅ |

**Result:** 181+ OTEL trace events in `otel-rt-logs` stream, sessions discoverable by evaluation.

---

## The Mistake That Cost Us 3 Deployments

When we switched from raw HTTP server to `BedrockAgentCoreApp`, we changed the Dockerfile CMD:

```dockerfile
# ❌ v20-v21: No OTEL traces exported
CMD ["python", "main.py"]

# ✅ v28: OTEL traces restored
CMD ["opentelemetry-instrument", "python", "main.py"]
```

**Impact:** All invocations between v20-v27 worked fine (agent responded correctly) but were **invisible to evaluation** — no spans exported, no sessions discoverable.

**Lesson:** Always verify OTEL is actually exporting by checking the `otel-rt-logs` stream after each deployment change.

---

## References

### Official AWS Documentation
- [Getting started with on-demand evaluation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/getting-started-on-demand.html)
- [Supported frameworks & telemetry](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/supported-frameworks-telemetry.html)
- [Strands Agents instrumentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/supported-frameworks-strands.html)
- [Evaluation results format (OTEL semantic conventions)](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/results-and-output.html)
- [A/B testing with OTEL for agents outside AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ab-testing-3p-agents.html)
- [AgentCore Evaluations built-in evaluators](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html)
- [Batch evaluation results in CloudWatch](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/batch-evaluations-results.html)
- [EvaluationInput API reference](https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/API_EvaluationInput.html)

### AWS Blog
- [Build trustworthy AI agents with Amazon Bedrock AgentCore Observability](https://aws.amazon.com/blogs/machine-learning/build-trustworthy-ai-agents-with-amazon-bedrock-agentcore-observability/)

### GitHub Samples
- [AgentCore Evaluation Samples (awslabs)](https://github.com/awslabs/agentcore-samples/tree/main/01-features/06-observe-evaluate-optimize-your-agent/02-evaluate)
  - [`ground-truth-based-evaluation/`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/06-observe-evaluate-optimize-your-agent/02-evaluate/ground-truth-based-evaluation) — EvaluationClient + DatasetRunner + BatchRunner
  - [`llm-as-a-judge-evaluation/`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/06-observe-evaluate-optimize-your-agent/02-evaluate/llm-as-a-judge-evaluation) — Custom LLM-as-Judge evaluators
  - [`custom-code-based-evaluation/`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/06-observe-evaluate-optimize-your-agent/02-evaluate/custom-code-based-evaluation) — Lambda-backed evaluators
  - [`supported-frameworks/`](https://github.com/awslabs/agentcore-samples/tree/main/01-features/06-observe-evaluate-optimize-your-agent/02-evaluate/supported-frameworks) — OpenAI Agents SDK, LlamaIndex

### This Repository
- [LLMOps Pipeline Agent (GitHub)](https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore)
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — All 17 errors documented
- [TEST_PROMPTS.md](./TEST_PROMPTS.md) — 20 test prompts for verification

---

## What's Next

With OTEL traces flowing and evaluation configured, you can:
1. **Run batch evaluation** across multiple sessions for aggregate quality scores
2. **Set up online evaluation** for continuous production monitoring
3. **Create custom evaluators** for domain-specific quality (DevOps accuracy, tool selection, diagnosis quality)
4. **Add evaluation as a CI/CD quality gate** — block deployments if quality drops below threshold

---

**GitHub:** https://github.com/catchmeraman/LLMOps-Pipeline-AgentCore
