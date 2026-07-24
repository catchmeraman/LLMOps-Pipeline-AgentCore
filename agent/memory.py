"""
Memory module for LLMOps Agent.
Provides cross-session persistence using AgentCore Memory / DynamoDB.
"""
import boto3
import json
import logging
from datetime import datetime

logger = logging.getLogger("llmops.memory")

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')


class AgentMemory:
    """Cross-session memory for the LLMOps agent.
    
    Stores:
    - User preferences (response format, verbosity)
    - Session context (last actions taken, pending tasks)
    - Learned patterns (common issues and resolutions for this user)
    """

    def __init__(self, table_name: str = "llmops-agent-memory"):
        self.table_name = table_name
        self._ensure_table()

    def _ensure_table(self):
        """Create DynamoDB table if it doesn't exist."""
        try:
            self.table = dynamodb.Table(self.table_name)
            self.table.load()
        except Exception:
            try:
                dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {"AttributeName": "user_id", "KeyType": "HASH"},
                        {"AttributeName": "memory_key", "KeyType": "RANGE"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "user_id", "AttributeType": "S"},
                        {"AttributeName": "memory_key", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST"
                )
                self.table = dynamodb.Table(self.table_name)
                logger.info(f"Created memory table: {self.table_name}")
            except Exception as e:
                logger.warning(f"Could not create memory table: {e}")
                self.table = None

    def remember(self, user_id: str, key: str, value: str, category: str = "general"):
        """Store a memory that persists across sessions."""
        if not self.table:
            return
        try:
            self.table.put_item(Item={
                "user_id": user_id,
                "memory_key": f"{category}#{key}",
                "value": value,
                "category": category,
                "timestamp": datetime.utcnow().isoformat(),
                "ttl": int(datetime.utcnow().timestamp()) + (90 * 86400)  # 90 day TTL
            })
            logger.info(f"Memory stored: {user_id}/{category}/{key}")
        except Exception as e:
            logger.warning(f"Failed to store memory: {e}")

    def recall(self, user_id: str, category: str = None) -> list:
        """Recall memories for a user, optionally filtered by category."""
        if not self.table:
            return []
        try:
            if category:
                response = self.table.query(
                    KeyConditionExpression="user_id = :uid AND begins_with(memory_key, :cat)",
                    ExpressionAttributeValues={":uid": user_id, ":cat": f"{category}#"}
                )
            else:
                response = self.table.query(
                    KeyConditionExpression="user_id = :uid",
                    ExpressionAttributeValues={":uid": user_id}
                )
            return [
                {"key": item["memory_key"].split("#", 1)[-1], "value": item["value"],
                 "category": item.get("category"), "timestamp": item.get("timestamp")}
                for item in response.get("Items", [])
            ]
        except Exception as e:
            logger.warning(f"Failed to recall memory: {e}")
            return []

    def recall_as_context(self, user_id: str) -> str:
        """Format all memories as context string for the agent's system prompt."""
        memories = self.recall(user_id)
        if not memories:
            return ""

        context_lines = ["## User Memory (from previous sessions):"]
        for mem in memories[-10:]:  # Last 10 memories
            context_lines.append(f"- [{mem['category']}] {mem['key']}: {mem['value']}")

        return "\n".join(context_lines)

    def forget(self, user_id: str, key: str, category: str = "general"):
        """Remove a specific memory."""
        if not self.table:
            return
        try:
            self.table.delete_item(Key={"user_id": user_id, "memory_key": f"{category}#{key}"})
        except Exception as e:
            logger.warning(f"Failed to forget: {e}")
