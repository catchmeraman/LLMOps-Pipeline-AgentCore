"""LLMOps Agent — Main entry point for AgentCore Runtime (port 8080)."""
import json
import logging
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
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
            session_id = request.get("session_id", "default")

            logger.info(f"[session={session_id}] Received: {prompt[:100]}...")
            response = agent(prompt)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": str(response),
                "session_id": session_id,
                "status": "success"
            }).encode())
            logger.info(f"[session={session_id}] Completed successfully")

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
        self.wfile.write(json.dumps({"status": "healthy", "agent": "llmops-agent", "version": "1.0"}).encode())

    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), AgentHandler)
    logger.info("LLMOps Agent starting on port 8080")
    logger.info("Ready to receive requests from AgentCore Runtime")
    server.serve_forever()
