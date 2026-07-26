# 📸 Screenshots — Capture These for Ambassador Blog

> Replace each placeholder with actual console screenshots.
> Name files exactly as listed. Commit and push after capturing.

---

## Required Screenshots (22)

### AgentCore Runtime (v11)
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 1 | `01_runtime_dashboard.png` | Runtime list showing llmops_agent READY v11 | Bedrock → AgentCore → Runtimes |
| 2 | `02_runtime_config.png` | Configuration (container URI, role, env vars) | Click llmops_agent → Configuration |
| 3 | `03_runtime_versions.png` | Version history v1→v11 | Click llmops_agent → Versions |
| 4 | `04_runtime_endpoints.png` | DEFAULT endpoint | Click llmops_agent → Endpoints |

### Guardrails
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 5 | `05_guardrail_config.png` | LLMOps-Agent-Guardrail settings | Bedrock → Guardrails → LLMOps-Agent-Guardrail |
| 6 | `06_guardrail_content_filter.png` | Content filter (PROMPT_ATTACK=HIGH) | Guardrail → Content filters |
| 7 | `07_guardrail_pii.png` | PII filter (SSN=BLOCK, Email=ANONYMIZE) | Guardrail → Sensitive info |
| 8 | `08_guardrail_test_blocked.png` | BLOCKED prompt injection test | Guardrail → Test → Type injection |

### Evaluations (BOTH Container + Harness Working)
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 9 | `09_evaluators_list.png` | All evaluators (built-in + 4 custom Nova Pro) | AgentCore → Evaluations → Evaluators |
| 10 | `10_custom_evaluator_config.png` | llmopsDevOpsQuality showing Nova Pro model | Click custom evaluator → config |
| 11 | `11_online_eval_config.png` | Online eval (9 evaluators, 100% sampling) | AgentCore → Evaluations → Online |
| 12 | `12_evaluation_results.png` | **Batch eval scores on Container runtime** | AgentCore → Evaluations → Batch runs |
| 12b | `12b_harness_eval_results.png` | **Batch eval scores on Harness runtime** | Same → select harness job |
| 13b | `13b_eval_scores_detail.png` | Score breakdown per evaluator | Click a batch job → results |

### CI/CD
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 13 | `13_codebuild_history.png` | 9+ successful builds (all green) | CodeBuild → llmops-agent-build → History |
| 14 | `14_codebuild_phases.png` | Build phases (Source→Build→Push) | Click a build → Phases |
| 15 | `15_ecr_images.png` | Docker images in ECR | ECR → bedrock-agentcore-llmops-agent |

### Observability & Traces
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 16 | `16_cloudwatch_logs.png` | Runtime log streams (627+) | CloudWatch → Log groups → llmops_agent |
| 16b | `16b_otel_traces.png` | **otel-rt-logs stream** with JSON OTEL traces | Same log group → otel-rt-logs stream |
| 17 | `17_trace_with_session_id.png` | Trace showing session.id and real trace_id | Expand an otel-rt-logs event |

### Infrastructure
| # | Filename | What to Capture | Console Path |
|---|----------|-----------------|-------------|
| 18 | `18_iam_role_permissions.png` | event-agent-role (15+ policies) | IAM → Roles → event-agent-role |
| 19 | `19_dynamodb_memory.png` | llmops-agent-memory table | DynamoDB → Tables |
| 20 | `20_s3_artifacts.png` | S3 source.zip | S3 → event-agent-kb → llmops-pipeline/ |

---

## Key Screenshots for Ambassador Application

**Most important (proves it works end-to-end):**
1. `12_evaluation_results.png` — Container runtime evaluation SCORING ✅
2. `12b_harness_eval_results.png` — Harness evaluation SCORING ✅
3. `08_guardrail_test_blocked.png` — Security working
4. `16b_otel_traces.png` — OTEL traces with session.id
5. `10_custom_evaluator_config.png` — Custom evaluator with YOUR model choice
6. `13_codebuild_history.png` — CI/CD pipeline green
