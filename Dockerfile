FROM public.ecr.aws/docker/library/python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/main.py agent/agent.py agent/guardrails.py agent/memory.py agent/observability.py agent/skills.py ./
COPY agent/tools/ ./tools/

EXPOSE 8080

CMD ["opentelemetry-instrument", "python", "main.py"]
