"""LLMOps Agent — Main entry point for AgentCore Runtime (port 8080)."""
import json
import logging
import traceback
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from opentelemetry import baggage, context
from agent import create_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("llmops-agent")

agent = create_agent()


class AgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            prompt = request.get("prompt", "")
            session_id = request.get("session_id", str(uuid.uuid4()))

            # Set session.id baggage for OTEL trace correlation
            ctx = baggage.set_baggage("session.id", session_id)
            token = context.attach(ctx)

            logger.info(f"[session={session_id}] Received: {prompt[:100]}...")

            try:
                response = agent(prompt)
            finally:
                context.detach(token)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            result = {
                "response": str(response),
                "session_id": session_id,
                "status": "success"
            }
            self.wfile.write(json.dumps(result).encode())
            logger.info(f"[session={session_id}] Completed successfully")

        except Exception as e:
            logger.error(f"Agent error: {e}\n{traceback.format_exc()}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            error_result = {"error": str(e), "status": "error"}
            self.wfile.write(json.dumps(error_result).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "healthy", "agent": "llmops-agent", "version": "1.0"}).encode())

    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), AgentHandler)
    logger.info("LLMOps Agent starting on port 8080")
    logger.info("Ready to receive requests from AgentCore Runtime")
    server.serve_forever()
