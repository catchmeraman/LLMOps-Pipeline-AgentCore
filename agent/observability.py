"""
Observability module for LLMOps Agent.
Structured JSON logging + CloudWatch custom metrics for every invocation.
"""
import boto3
import json
import time
import logging
from datetime import datetime
from functools import wraps

cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
logger = logging.getLogger("llmops.observability")
logger.setLevel(logging.INFO)

NAMESPACE = "LLMOps/Agent"
AGENT_NAME = "llmops-agent"


class ObservabilityLayer:
    """Tracks latency, tokens, cost, errors for every invocation."""

    def __init__(self, agent_name: str = AGENT_NAME):
        self.agent_name = agent_name
        self.invocation_count = 0
        self.error_count = 0

    def wrap_invocation(self, agent, prompt: str, **kwargs) -> dict:
        """Invoke agent with full observability tracking."""
        self.invocation_count += 1
        start = time.time()
        error = None
        result = None
        session_id = kwargs.get("session_id", "unknown")
        user_id = kwargs.get("user_id", "anonymous")

        try:
            result = agent(prompt)
            return result
        except Exception as e:
            error = str(e)
            self.error_count += 1
            raise
        finally:
            duration_ms = (time.time() - start) * 1000
            self._log_invocation(prompt, result, duration_ms, error, session_id, user_id)
            self._emit_metrics(duration_ms, error)

    def _log_invocation(self, prompt, result, duration_ms, error, session_id, user_id):
        """Structured JSON log for every invocation."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR" if error else "INFO",
            "agent": self.agent_name,
            "event": "invocation",
            "session_id": session_id,
            "user_id": user_id,
            "input_length": len(prompt),
            "output_length": len(str(result)) if result else 0,
            "duration_ms": round(duration_ms, 1),
            "error": error,
            "invocation_number": self.invocation_count
        }
        logger.info(json.dumps(log_entry))

    def _emit_metrics(self, duration_ms: float, error: str = None):
        """Publish custom metrics to CloudWatch."""
        dimensions = [{"Name": "Agent", "Value": self.agent_name}]
        timestamp = datetime.utcnow()

        metrics = [
            {"MetricName": "InvocationLatencyMs", "Value": duration_ms,
             "Unit": "Milliseconds", "Dimensions": dimensions, "Timestamp": timestamp},
            {"MetricName": "InvocationCount", "Value": 1,
             "Unit": "Count", "Dimensions": dimensions, "Timestamp": timestamp},
        ]

        if error:
            metrics.append({
                "MetricName": "ErrorCount", "Value": 1,
                "Unit": "Count", "Dimensions": dimensions, "Timestamp": timestamp
            })

        try:
            cloudwatch.put_metric_data(Namespace=NAMESPACE, MetricData=metrics)
        except Exception as e:
            logger.warning(f"Failed to emit metrics: {e}")

    def create_dashboard(self):
        """Create CloudWatch dashboard for the agent."""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric", "x": 0, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "title": "Invocation Latency (ms)",
                        "metrics": [[NAMESPACE, "InvocationLatencyMs", "Agent", self.agent_name]],
                        "period": 60, "stat": "Average", "region": "us-east-1"
                    }
                },
                {
                    "type": "metric", "x": 12, "y": 0, "width": 12, "height": 6,
                    "properties": {
                        "title": "Invocations & Errors",
                        "metrics": [
                            [NAMESPACE, "InvocationCount", "Agent", self.agent_name],
                            [NAMESPACE, "ErrorCount", "Agent", self.agent_name]
                        ],
                        "period": 60, "stat": "Sum", "region": "us-east-1"
                    }
                },
                {
                    "type": "metric", "x": 0, "y": 6, "width": 12, "height": 6,
                    "properties": {
                        "title": "Evaluation Scores",
                        "metrics": [
                            ["LLMOps/Evaluation", "OverallPassRate", "Agent", self.agent_name],
                            ["LLMOps/Evaluation", "FunctionalAvgScore", "Agent", self.agent_name]
                        ],
                        "period": 3600, "stat": "Average", "region": "us-east-1"
                    }
                }
            ]
        }

        try:
            cloudwatch.put_dashboard(
                DashboardName=f"LLMOps-{self.agent_name}",
                DashboardBody=json.dumps(dashboard_body)
            )
            logger.info(f"Dashboard created: LLMOps-{self.agent_name}")
        except Exception as e:
            logger.warning(f"Failed to create dashboard: {e}")

    def create_alarms(self, sns_topic_arn: str):
        """Create CloudWatch alarms for the agent."""
        alarms = [
            {
                "AlarmName": f"llmops-{self.agent_name}-high-latency",
                "MetricName": "InvocationLatencyMs",
                "Threshold": 10000,
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 3,
                "Period": 60,
                "Statistic": "Average",
                "AlarmDescription": "Agent latency > 10 seconds for 3 consecutive minutes"
            },
            {
                "AlarmName": f"llmops-{self.agent_name}-errors",
                "MetricName": "ErrorCount",
                "Threshold": 3,
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "Period": 300,
                "Statistic": "Sum",
                "AlarmDescription": "More than 3 errors in 10 minutes"
            }
        ]

        for alarm in alarms:
            try:
                cloudwatch.put_metric_alarm(
                    AlarmName=alarm["AlarmName"],
                    Namespace=NAMESPACE,
                    MetricName=alarm["MetricName"],
                    Dimensions=[{"Name": "Agent", "Value": self.agent_name}],
                    Threshold=alarm["Threshold"],
                    ComparisonOperator=alarm["ComparisonOperator"],
                    EvaluationPeriods=alarm["EvaluationPeriods"],
                    Period=alarm["Period"],
                    Statistic=alarm["Statistic"],
                    AlarmActions=[sns_topic_arn],
                    AlarmDescription=alarm["AlarmDescription"]
                )
            except Exception as e:
                logger.warning(f"Failed to create alarm {alarm['AlarmName']}: {e}")

        logger.info(f"Created {len(alarms)} monitoring alarms")
