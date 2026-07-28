"""LLMOps Agent — Main entry point for AgentCore Runtime (port 8080).
Integrates: Guardrails (input/output) + Dual Memory (AgentCore + DynamoDB) + OTEL session baggage."""
import json
import logging
import traceback
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from opentelemetry import baggage, context
from agent import create_agent
from guardrails import BedrockGuardrails
from memory import DualMemory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("llmops-agent")

agent = create_agent()
guardrails = BedrockGuardrails()
memory = DualMemory()


class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            prompt = request.get("prompt", "")
            session_id = request.get("session_id", str(uuid.uuid4()))
            user_id = request.get("user_id", "default-user")

            # Set session.id baggage for OTEL trace correlation
            ctx = baggage.set_baggage("session.id", session_id)
            token = context.attach(ctx)

            logger.info(f"[session={session_id}] [user={user_id}] Received: {prompt[:100]}...")

            try:
                # === GUARDRAIL: Check input BEFORE agent ===
                input_check = guardrails.check_input(prompt)
                if not input_check["allowed"]:
                    logger.warning(f"[session={session_id}] GUARDRAIL BLOCKED: {input_check['reasons']}")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "response": input_check["safe_response"],
                        "session_id": session_id,
                        "status": "blocked",
                        "guardrail": "input_blocked",
                        "reasons": input_check["reasons"]
                    }).encode())
                    return

                # === DUAL MEMORY: Build context from both AgentCore + DynamoDB ===
                memory_context = memory.build_context(user_id, prompt)
                if memory_context:
                    logger.info(f"[session={session_id}] Dual memory context loaded (AgentCore + DynamoDB)")
                    full_prompt = f"{memory_context}\n\nCurrent request: {prompt}"
                else:
                    full_prompt = prompt

                # === AGENT: Invoke with validated input + memory context ===
                response = agent(full_prompt)
                response_text = str(response)

                # === DUAL MEMORY: Store interaction in both backends ===
                memory.store_interaction(user_id, session_id, prompt, response_text)

                # === GUARDRAIL: Check output BEFORE returning to user ===
                output_check = guardrails.check_output(response_text)
                if output_check["modified"]:
                    logger.info(f"[session={session_id}] GUARDRAIL modified output (PII redacted)")
                    response_text = output_check["text"]

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "response": response_text,
                    "session_id": session_id,
                    "user_id": user_id,
                    "status": "success",
                    "memory_used": bool(memory_context),
                    "memory_backends": ["agentcore", "dynamodb"],
                    "guardrail": "output_modified" if output_check["modified"] else "passed"
                }).encode())
                logger.info(f"[session={session_id}] Completed (memory={'dual' if memory_context else 'none'})")

            finally:
                context.detach(token)

        except Exception as e:
            logger.error(f"Agent error: {e}\n{traceback.format_exc()}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "status": "error"}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "healthy",
            "agent": "llmops-pipeline-agent",
            "version": "2.0",
            "guardrail": "attached (input + output)",
            "memory": {
                "architecture": "dual",
                "agentcore": f"attached ({memory.agentcore.memory_id})",
                "dynamodb": f"attached ({memory.dynamodb.table_name})"
            }
        }).encode())

    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), AgentHandler)
    logger.info("=" * 60)
    logger.info("LLMOps Pipeline Agent v2.0 starting on port 8080")
    logger.info("=" * 60)
    logger.info("Guardrails: ATTACHED (input + output screening)")
    logger.info("Memory: DUAL ARCHITECTURE")
    logger.info("  → AgentCore Memory: conversation context (semantic)")
    logger.info("  → DynamoDB Memory:  user preferences (structured)")
    logger.info("Ready to receive requests from AgentCore Runtime")
    logger.info("=" * 60)
    server.serve_forever()
