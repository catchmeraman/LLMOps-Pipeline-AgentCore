"""LLMOps Agent — HTTP server for AgentCore Runtime with full production features."""
import json
import logging
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from agent.agent import create_agent
from agent.observability import ObservabilityLayer
from agent.memory import AgentMemory

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("bedrock_agentcore.app")

agent = None
observability = ObservabilityLayer(agent_name="llmops-agent")
memory = AgentMemory(table_name="llmops-agent-memory")


def get_agent():
    global agent
    if agent is None:
        agent = create_agent()
    return agent


class AgentHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        from agent.skills import AGENT_SKILLS
        self.wfile.write(json.dumps({
            "status": "healthy",
            "agent": AGENT_SKILLS["metadata"]["agent_name"],
            "version": AGENT_SKILLS["metadata"]["version"],
            "skills_count": len(AGENT_SKILLS["skills"]),
            "guardrail_id": AGENT_SKILLS["metadata"]["guardrail_id"],
            "runtime_id": AGENT_SKILLS["metadata"]["runtime_id"]
        }).encode())

    def do_POST(self):
        start = time.time()
        content_length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_length)) if content_length else {}
        prompt = body.get("prompt", body.get("input", ""))
        session_id = self.headers.get("X-Session-Id", "default")
        user_id = self.headers.get("X-User-Id", "anonymous")

        try:
            # Recall user memory context
            memory_context = memory.recall_as_context(user_id)
            full_prompt = f"{memory_context}\n\n{prompt}" if memory_context else prompt

            # Invoke with observability
            result = observability.wrap_invocation(
                get_agent(), full_prompt,
                session_id=session_id, user_id=user_id
            )

            duration = time.time() - start
            logger.info(f"Invocation completed ({duration:.3f}s) session={session_id} user={user_id}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": str(result),
                "session_id": session_id,
                "user_id": user_id,
                "duration_ms": round(duration * 1000, 1),
                "memory_used": bool(memory_context)
            }).encode())
        except Exception as e:
            logger.error(f"Invocation failed: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), AgentHandler)
    logger.info("LLMOps Agent v1.0 running on port 8080 (with observability + memory)")
    server.serve_forever()
