"""LLMOps Agent — Main entry point for AgentCore Runtime.
Uses BedrockAgentCoreApp (SDK entrypoint) with Guardrails + Dual Memory."""
import json
import logging
import traceback
import uuid

from agent import create_agent
from guardrails import BedrockGuardrails
from memory import DualMemory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("llmops-agent")

agent = create_agent()
guardrails = BedrockGuardrails()
memory = DualMemory()

logger.info("=" * 60)
logger.info("LLMOps Pipeline Agent v2.0")
logger.info("=" * 60)
logger.info("Guardrails: ATTACHED (input + output screening)")
logger.info("Memory: DUAL ARCHITECTURE")
logger.info("  → AgentCore Memory: conversation context (semantic)")
logger.info("  → DynamoDB Memory:  user preferences (structured)")
logger.info("=" * 60)


def handle_request(prompt: str, user_id: str, session_id: str) -> dict:
    """Process a single agent request with guardrails + memory."""
    try:
        # === GUARDRAIL: Check input BEFORE agent ===
        input_check = guardrails.check_input(prompt)
        if not input_check["allowed"]:
            logger.warning(f"[session={session_id}] GUARDRAIL BLOCKED: {input_check['reasons']}")
            return {
                "response": input_check["safe_response"],
                "session_id": session_id,
                "status": "blocked",
                "guardrail": "input_blocked",
                "reasons": input_check["reasons"]
            }

        # === DUAL MEMORY: Build context from both AgentCore + DynamoDB ===
        memory_context = memory.build_context(user_id, prompt)
        if memory_context:
            logger.info(f"[session={session_id}] Dual memory context loaded")
            full_prompt = f"{memory_context}\n\nCurrent request: {prompt}"
        else:
            full_prompt = prompt

        # === AGENT: Invoke with validated input + memory context ===
        response = agent(full_prompt)
        response_text = str(response)

        # === DUAL MEMORY: Store interaction in both backends ===
        memory.store_interaction(user_id, session_id, prompt, response_text)

        # === GUARDRAIL: Check output BEFORE returning ===
        output_check = guardrails.check_output(response_text)
        if output_check["modified"]:
            logger.info(f"[session={session_id}] GUARDRAIL modified output")
            response_text = output_check["text"]

        logger.info(f"[session={session_id}] Completed (memory={'dual' if memory_context else 'none'})")
        return {
            "response": response_text,
            "session_id": session_id,
            "user_id": user_id,
            "status": "success",
            "memory_used": bool(memory_context),
            "memory_backends": ["agentcore", "dynamodb"],
            "guardrail": "output_modified" if output_check["modified"] else "passed"
        }

    except Exception as e:
        logger.error(f"Agent error: {e}\n{traceback.format_exc()}")
        return {"error": str(e), "status": "error"}


# ── AgentCore Runtime entrypoint ──
try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    app = BedrockAgentCoreApp()

    @app.entrypoint
    def runtime_handler(payload, context):
        if isinstance(payload, (bytes, bytearray)):
            payload = json.loads(payload.decode("utf-8"))
        elif isinstance(payload, str):
            payload = json.loads(payload)

        prompt = payload.get("prompt", payload.get("query", ""))
        user_id = payload.get("user_id", payload.get("actor_id", "default-user"))
        session_id = payload.get("session_id", str(uuid.uuid4()))

        if not prompt:
            return json.dumps({"response": "Please provide a prompt.", "status": "error"})

        logger.info(f"[session={session_id}] [user={user_id}] Received: {prompt[:100]}...")

        result = handle_request(prompt, user_id, session_id)

        # Return in format compatible with AIEOS frontend: [response, tool_calls, model_info]
        return json.dumps([
            result.get("response", str(result)),
            [],
            {"model": "Nova Pro", "tokens": {"input": 0, "output": 0}}
        ])

    if __name__ == "__main__":
        app.run()

except ImportError:
    # Fallback: raw HTTP server (for local testing)
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class AgentHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            request = json.loads(body)
            result = handle_request(
                request.get("prompt", ""),
                request.get("user_id", "default-user"),
                request.get("session_id", str(uuid.uuid4()))
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "agent": "llmops-pipeline-agent", "version": "2.0"}).encode())

    if __name__ == "__main__":
        server = HTTPServer(("0.0.0.0", 8080), AgentHandler)
        logger.info("Running in HTTP fallback mode on port 8080")
        server.serve_forever()
