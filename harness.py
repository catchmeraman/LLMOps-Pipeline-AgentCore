"""
Harness Script — Invoke, Test, and Evaluate the deployed LLMOps Agent.
Connects to AgentCore Runtime and runs the full evaluation suite.

Usage:
  python harness.py --mode invoke --prompt "Check all alarms"
  python harness.py --mode evaluate
  python harness.py --mode smoke
  python harness.py --mode skills
"""
import argparse
import boto3
import json
import time
import sys
from datetime import datetime

# Agent configuration
AGENT_RUNTIME_ID = "llmops_agent-jgErJt74Gu"
REGION = "us-east-1"
ENDPOINT_NAME = "DEFAULT"

bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=REGION)


def invoke_agent(prompt: str, session_id: str = None) -> dict:
    """Invoke the deployed agent via AgentCore Runtime."""
    if not session_id:
        session_id = f"harness-{int(time.time())}"

    start = time.time()
    try:
        response = bedrock_agentcore.invoke_agent_runtime(
            agentRuntimeId=AGENT_RUNTIME_ID,
            agentRuntimeEndpointName=ENDPOINT_NAME,
            sessionId=session_id,
            inputText=prompt
        )

        # Read streaming response
        output_text = ""
        if 'body' in response:
            for event in response['body']:
                if 'chunk' in event:
                    output_text += event['chunk'].get('text', '')

        duration_ms = (time.time() - start) * 1000

        return {
            "response": output_text,
            "session_id": session_id,
            "duration_ms": round(duration_ms, 1),
            "status": "success"
        }
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        return {
            "response": str(e),
            "session_id": session_id,
            "duration_ms": round(duration_ms, 1),
            "status": "error",
            "error": str(e)
        }


def invoke_for_eval(prompt: str) -> str:
    """Simple invoke that returns just the text (for evaluator)."""
    result = invoke_agent(prompt)
    return result.get("response", result.get("error", ""))


def run_smoke_tests():
    """Quick smoke test to verify the agent is responding."""
    print("🔥 Running Smoke Tests...")
    print("=" * 50)

    tests = [
        {"name": "Health Check", "prompt": "Hello, what can you do?"},
        {"name": "Alarm Check", "prompt": "Check CloudWatch alarms in ALARM state"},
        {"name": "Instance List", "prompt": "List all EC2 instances"},
    ]

    passed = 0
    for test in tests:
        print(f"\n  📋 {test['name']}...")
        result = invoke_agent(test["prompt"])
        is_pass = result["status"] == "success" and len(result["response"]) > 20
        icon = "✅" if is_pass else "❌"
        print(f"  {icon} Status: {result['status']} | Duration: {result['duration_ms']}ms")
        print(f"     Response: {result['response'][:100]}...")
        if is_pass:
            passed += 1

    print(f"\n{'='*50}")
    print(f"  Smoke Tests: {passed}/{len(tests)} passed")
    return passed == len(tests)


def run_full_evaluation():
    """Run the complete evaluation suite (guardrails + functional)."""
    from evaluation.evaluator import AgentEvaluator

    evaluator = AgentEvaluator()
    summary = evaluator.run_full_evaluation(invoke_for_eval)

    # Save results
    results_file = f"/tmp/eval_results_{summary['run_id']}.json"
    with open(results_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n📄 Results saved: {results_file}")

    return summary["gate_passed"]


def show_skills():
    """Display all agent skills."""
    from agent.skills import get_skill_summary
    print(get_skill_summary())


def interactive_mode():
    """Interactive chat with the deployed agent."""
    print("🤖 LLMOps Agent — Interactive Mode")
    print("    Type 'exit' to quit, 'eval' to run evaluation")
    print("=" * 50)

    session_id = f"interactive-{int(time.time())}"

    while True:
        prompt = input("\n🧑 You: ").strip()
        if not prompt:
            continue
        if prompt.lower() in ['exit', 'quit']:
            break
        if prompt.lower() == 'eval':
            run_full_evaluation()
            continue
        if prompt.lower() == 'skills':
            show_skills()
            continue

        result = invoke_agent(prompt, session_id=session_id)
        print(f"\n🤖 Agent ({result['duration_ms']}ms): {result['response']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLMOps Agent Harness")
    parser.add_argument("--mode", choices=["invoke", "evaluate", "smoke", "skills", "interactive"],
                       default="interactive", help="Harness mode")
    parser.add_argument("--prompt", type=str, help="Prompt for invoke mode")
    args = parser.parse_args()

    if args.mode == "invoke":
        if not args.prompt:
            print("Error: --prompt required for invoke mode")
            sys.exit(1)
        result = invoke_agent(args.prompt)
        print(json.dumps(result, indent=2))

    elif args.mode == "evaluate":
        passed = run_full_evaluation()
        sys.exit(0 if passed else 1)

    elif args.mode == "smoke":
        passed = run_smoke_tests()
        sys.exit(0 if passed else 1)

    elif args.mode == "skills":
        show_skills()

    elif args.mode == "interactive":
        interactive_mode()
