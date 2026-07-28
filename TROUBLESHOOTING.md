# 🔧 Troubleshooting Guide — LLMOps Pipeline Agent

> Every error hit during the build from v14 → v24, with root cause and fix.

---

## CI/CD Pipeline Errors

### 1. YAML_FILE_ERROR in buildspec.yml
```
DOWNLOAD_SOURCE FAILED
Expected Commands[7] to be of string type: found subkeys instead at line 25
```
**Root Cause:** Multi-line `|` blocks in buildspec post_build commands don't work well with CodeBuild's YAML parser when used inside pipeline artifacts.

**Fix:** Replace multi-line blocks with single-line Python commands:
```yaml
# ❌ BAD — multi-line block
- |
  python3 -c "
  import boto3
  ...
  "

# ✅ GOOD — single line
- python3 -c "import boto3; client=boto3.client('bedrock-agentcore-control'); ..."
```

---

### 2. CodeCommit push 403 Forbidden
```
fatal: unable to access 'https://git-codecommit.us-east-1.amazonaws.com/v1/repos/...' 403
```
**Root Cause:** Local git credential helper not configured for CodeCommit, or IAM user lacks `codecommit:GitPush` permission.

**Fix:** Use CodeCommit API directly:
```bash
aws codecommit create-commit \
  --repository-name llmops-pipeline-agent \
  --branch-name main \
  --parent-commit-id $(aws codecommit get-branch ...) \
  --put-files "filePath=file.py,fileMode=NORMAL,fileContent=$(base64 -i file.py)"
```

---

### 3. EventBridge trigger — CodeStarSourceConnection error
```
InvalidStructureException: Triggers for connections must reference a CodeStarSourceConnection action
```
**Root Cause:** V2 pipeline `triggers` with `providerType: CodeStarSourceConnection` only works with GitHub/GitLab connections, NOT CodeCommit.

**Fix:** Remove explicit trigger. Create an EventBridge rule instead:
```json
{
  "source": ["aws.codecommit"],
  "detail-type": ["CodeCommit Repository State Change"],
  "detail": {"event": ["referenceUpdated"], "referenceName": ["main"]}
}
```

---

### 4. Docker build failed — wrong package name
```
BUILD phase FAILED: docker build -t $ECR_REPO:$IMAGE_TAG . Reason: exit status 1
```
**Root Cause:** `bedrock-agentcore-runtime>=0.1.0` doesn't exist. Correct package is `bedrock-agentcore>=1.0.0`.

**Fix:** In `requirements.txt`:
```
bedrock-agentcore>=1.0.0    # ✅ Correct
# bedrock-agentcore-runtime  # ❌ Doesn't exist
```

---

## Runtime / Container Errors

### 5. ModuleNotFoundError: No module named 'guardrails'
```
File "/app/main.py", line 10, in <module>
    from guardrails import BedrockGuardrails
ModuleNotFoundError: No module named 'guardrails'
```
**Root Cause:** `Dockerfile` COPY line was missing `agent/guardrails.py`.

**Fix:**
```dockerfile
# ❌ Missing guardrails.py
COPY agent/main.py agent/agent.py agent/observability.py agent/memory.py agent/skills.py ./

# ✅ Include all modules
COPY agent/main.py agent/agent.py agent/guardrails.py agent/memory.py agent/observability.py agent/skills.py ./
```

---

### 6. ValueError: Propagator xray not found
```
ValueError: Propagator xray not found. It is either misspelled or not installed.
```
**Root Cause:** Environment variable `OTEL_PROPAGATORS=baggage,xray,tracecontext` requires `aws-opentelemetry-distro` which provides the xray propagator. Package was removed from requirements.txt.

**Fix:** Keep `aws-opentelemetry-distro` in requirements.txt:
```
aws-opentelemetry-distro>=0.10.0
```

---

### 7. RuntimeClientError — 500 from runtime (raw HTTP server)
```
An error occurred (RuntimeClientError) when calling the InvokeAgentRuntime operation: 
Received error (500) from runtime.
```
**Root Cause:** Agent used `BaseHTTPRequestHandler` on port 8080. AgentCore does NOT send plain HTTP — it uses the `bedrock-agentcore` SDK framework (`BedrockAgentCoreApp`).

**Fix:** Replace HTTP server with BedrockAgentCoreApp:
```python
# ❌ Raw HTTP — AgentCore can't route to this
from http.server import HTTPServer, BaseHTTPRequestHandler
server = HTTPServer(("0.0.0.0", 8080), AgentHandler)

# ✅ AgentCore SDK — proper routing
from bedrock_agentcore.runtime import BedrockAgentCoreApp
app = BedrockAgentCoreApp()

@app.entrypoint
def runtime_handler(payload, context):
    data = json.loads(payload)
    result = handle_request(data["prompt"], data["user_id"], data["session_id"])
    return json.dumps(result)

app.run()
```

---

### 8. AgentCore Memory — Invalid metadata type
```
Invalid type for parameter records[0].metadata.session_id, value: ..., type: <class 'str'>, valid types: <class 'dict'>
```
**Root Cause:** `batch_create_memory_records` `metadata` field expects dict values to be dicts, not plain strings.

**Fix:** Remove metadata or restructure:
```python
# ❌ BAD — string values in metadata
'metadata': {'session_id': session_id, 'actor': actor}

# ✅ GOOD — remove metadata, use namespaces for context
records=[{
    'requestIdentifier': str(uuid.uuid4()),
    'namespaces': [namespace],
    'content': {'text': content},
    'timestamp': datetime.utcnow().isoformat() + 'Z',
}]
```

---

## Guardrail Errors

### 9. ApplyGuardrail ValidationException — incorrect format
```
ValidationException: Guardrail was enabled but input is in incorrect format.
```
**Root Cause:** The `content` parameter format for `apply_guardrail` needs `qualifiers` field in newer API versions.

**Fix:** Add qualifiers and fail-open error handling:
```python
# Try with qualifiers first
content=[{"text": {"text": user_input, "qualifiers": ["query"]}}]

# Fallback without qualifiers
content=[{"text": {"text": user_input}}]

# If both fail, allow through (fail open)
return {"allowed": True}
```

---

### 10. Guardrail DRAFT version doesn't block aggressively
**Symptom:** Prompt injection test passes through guardrail without blocking.

**Root Cause:** `GUARDRAIL_VERSION=DRAFT` may have different thresholds than a published version. The model itself (Nova Pro) still refuses unsafe requests.

**Fix:** Publish the guardrail and use version number:
```bash
aws bedrock create-guardrail-version --guardrail-identifier efx0nvwgqber
# Returns version "1" — use that instead of DRAFT
```

---

## Frontend (Streamlit) Errors

### 11. ImportError: cannot import name 'AGENT_CATEGORIES'
```
ImportError: cannot import name 'AGENT_CATEGORIES' from 'config'
```
**Root Cause:** Config was rewritten without the `AGENT_CATEGORIES` dict that `app.py` imports.

**Fix:** Add to config.py:
```python
AGENT_CATEGORIES = {
    "Operations": ["🚀 AIEOS", "🔧 IT Ops"],
    "LLMOps": ["🧠 LLMOps"],
    "DevOps": ["🔄 Jenkins Migration", "🏗️ IaC Generator", "🔍 Observability/RCA"],
}
```

---

### 12. ImportError: cannot import name 'JENKINS_RUNTIME_ID'
```
ImportError: cannot import name 'JENKINS_RUNTIME_ID' from 'config'
```
**Root Cause:** app.py has a secondary import inside a function that pulls DevOps agent IDs not present in the new config.

**Fix:** Add all referenced runtime IDs to config.py (even if empty):
```python
JENKINS_RUNTIME_ID = "jenkins_migration_agent-rDjfWy6h7T"
IAC_RUNTIME_ID = "iac_generator_agent-A6IShgCkic"
RCA_RUNTIME_ID = "observability_rca_agent-5UJggK3TwO"
CICD_RUNTIME_ID = "cicd_orchestrator_agent-o6NSg4DgGi"
```

---

### 13. StreamlitDuplicateElementKey error
```
StreamlitDuplicateElementKey: multiple elements with key='agent_btn_runtime_id'
```
**Root Cause:** DevOps agents were appended OUTSIDE the AGENTS dict (after closing `}`), creating orphan entries. Streamlit saw `"runtime_id"` as the agent name key.

**Fix:** Rewrite config.py cleanly with all agents inside a single AGENTS dict:
```python
AGENTS = {
    "🚀 AIEOS": {...},
    "🔧 IT Ops": {...},
    "🧠 LLMOps": {...},
    "🔄 Jenkins Migration": {...},
    "🏗️ IaC Generator": {...},
    "🔍 Observability/RCA": {...},
}
```

---

### 14. Frontend showing stale/shared memory preferences
**Symptom:** LLMOps agent diagnostics shows 10 preferences from AIEOS shared memory.

**Root Cause:** `get_memory_info()` always queries the shared `event_agent_memory` regardless of selected agent.

**Fix:** Add per-agent memory routing:
```python
# In config.py — add memory_id per agent
"🧠 LLMOps": {
    ...
    "memory_id": "llmops_agent_memory-iLAWGd3iCh",
    "dynamodb_table": "llmops-agent-memory",
}

# In app.py — route diagnostics to correct memory
mem = get_agent_memory_info() if agent_has_own_memory else get_memory_info()
```

---

## AgentCore Memory Creation Errors

### 15. CreateMemory — name validation
```
ValidationException: Member must satisfy regular expression pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}
```
**Root Cause:** Memory name used hyphens (`llmops-agent-memory`). Only alphanumeric + underscores allowed.

**Fix:** Use underscores: `llmops_agent_memory`

---

### 16. CreateMemory — summary strategy namespace
```
ValidationException: Memory strategy session_summaries is of Summarization type requiring {sessionId} as a mandatory part of namespace
```
**Root Cause:** Summary strategies require `{sessionId}` template in namespaces for session-scoped summarization.

**Fix:**
```python
'summaryMemoryStrategy': {
    'name': 'session_summaries',
    'namespaces': ['{sessionId}']  # ✅ Required template
}
```

---

## IAM Permission Errors

### 17. Missing AgentCore Memory API permissions
**Symptom:** Runtime 500 error when trying to write to AgentCore Memory.

**Root Cause:** Runtime role only had DynamoDB permissions, not `bedrock-agentcore:BatchCreateMemoryRecords`.

**Fix:** Add to IAM policy:
```json
{
    "Effect": "Allow",
    "Action": [
        "bedrock-agentcore:BatchCreateMemoryRecords",
        "bedrock-agentcore:RetrieveMemoryRecords"
    ],
    "Resource": "arn:aws:bedrock-agentcore:us-east-1:*:memory/*"
}
```

---

## Quick Reference — Error → Fix

| # | Error | One-line Fix |
|---|-------|-------------|
| 1 | YAML multi-line in buildspec | Use single-line commands |
| 2 | CodeCommit 403 | Use `aws codecommit create-commit` API |
| 3 | CodeStarSourceConnection invalid | Use EventBridge rule for CodeCommit |
| 4 | Wrong pip package name | `bedrock-agentcore>=1.0.0` |
| 5 | No module 'guardrails' | Add to Dockerfile COPY line |
| 6 | xray propagator not found | Keep `aws-opentelemetry-distro` in reqs |
| 7 | Runtime 500 (HTTP server) | Use `BedrockAgentCoreApp` SDK |
| 8 | Memory metadata invalid type | Remove string metadata, use namespaces |
| 9 | ApplyGuardrail format error | Add `qualifiers` + fail-open handler |
| 10 | Guardrail DRAFT not blocking | Publish version, use version number |
| 11-13 | Frontend import/key errors | Clean rewrite of config.py |
| 14 | Stale shared memory in UI | Per-agent `dynamodb_table` routing |
| 15-16 | Memory creation validation | Underscores in names, `{sessionId}` in namespace |
| 17 | Missing IAM for memory API | Add `bedrock-agentcore:Batch*` to role |
