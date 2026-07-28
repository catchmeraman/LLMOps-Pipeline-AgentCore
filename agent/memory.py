"""
Dual Memory Architecture for LLMOps Agent.

Two complementary memory backends:
1. AgentCore Memory (managed) — Conversation context via semantic extraction + session summaries
2. DynamoDB (structured) — User preferences, action history, explicit key-value storage

Architecture:
┌─────────────────────────────────────────────────────────┐
│                    DualMemory                            │
├────────────────────────┬────────────────────────────────┤
│   AgentCore Memory     │        DynamoDB Memory         │
│  (Conversation AI)     │   (Structured Preferences)     │
├────────────────────────┼────────────────────────────────┤
│ • Semantic extraction  │ • User preferences             │
│ • Session summaries    │ • Action history log           │
│ • Context retrieval    │ • Explicit remember/recall     │
│ • Auto-consolidation   │ • TTL-based expiry (90 days)   │
└────────────────────────┴────────────────────────────────┘
"""
import boto3
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger("llmops.memory")

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
agentcore_client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Configuration
AGENTCORE_MEMORY_ID = "llmops_agent_memory-iLAWGd3iCh"
DYNAMODB_TABLE_NAME = "llmops-agent-memory"


class AgentCoreMemory:
    """AgentCore managed memory — handles conversation context automatically.
    
    Uses semantic extraction to remember important facts from conversations
    and generates session summaries for cross-session continuity.
    """

    def __init__(self, memory_id: str = AGENTCORE_MEMORY_ID):
        self.memory_id = memory_id
        self.client = agentcore_client

    def store_conversation_event(self, session_id: str, actor: str, content: str, namespace: str = "conversations"):
        """Store a conversation event for semantic extraction."""
        try:
            self.client.batch_create_memory_records(
                memoryId=self.memory_id,
                records=[{
                    'requestIdentifier': str(uuid.uuid4()),
                    'namespaces': [namespace],
                    'content': {'text': content},
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'metadata': {
                        'session_id': session_id,
                        'actor': actor
                    }
                }]
            )
            logger.info(f"[AgentCore Memory] Stored event: session={session_id[:8]} actor={actor}")
        except Exception as e:
            logger.warning(f"[AgentCore Memory] Failed to store: {e}")

    def retrieve_context(self, query: str, namespace: str = "conversations", top_k: int = 5) -> list:
        """Retrieve semantically relevant memories for the given query."""
        try:
            resp = self.client.retrieve_memory_records(
                memoryId=self.memory_id,
                searchCriteria={
                    'searchQuery': query,
                    'topK': top_k
                },
                namespace=namespace
            )
            records = resp.get('records', [])
            return [
                {
                    'content': r.get('content', {}).get('text', ''),
                    'score': r.get('score', 0),
                    'timestamp': r.get('timestamp', '')
                }
                for r in records
            ]
        except Exception as e:
            logger.warning(f"[AgentCore Memory] Retrieval failed: {e}")
            return []

    def get_context_string(self, query: str) -> str:
        """Format retrieved memories as a context string for the agent."""
        memories = self.retrieve_context(query)
        if not memories:
            return ""
        
        context_lines = ["## Relevant Context (from AgentCore Memory):"]
        for mem in memories:
            context_lines.append(f"- {mem['content']}")
        return "\n".join(context_lines)


class DynamoDBMemory:
    """DynamoDB structured memory — explicit user preferences and action history.
    
    Stores:
    - User preferences (response format, verbosity, notification settings)
    - Action history (what operations were performed, outcomes)
    - Explicit user-stored facts (things the user asked to remember)
    """

    def __init__(self, table_name: str = DYNAMODB_TABLE_NAME):
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
                logger.info(f"Created DynamoDB table: {self.table_name}")
            except Exception as e:
                logger.warning(f"Could not create DynamoDB table: {e}")
                self.table = None

    def remember(self, user_id: str, key: str, value: str, category: str = "general"):
        """Store a structured memory (preference, fact, or history entry)."""
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
            logger.info(f"[DynamoDB] Stored: {user_id}/{category}/{key}")
        except Exception as e:
            logger.warning(f"[DynamoDB] Failed to store: {e}")

    def recall(self, user_id: str, category: str = None) -> list:
        """Recall structured memories for a user."""
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
            logger.warning(f"[DynamoDB] Failed to recall: {e}")
            return []

    def recall_as_context(self, user_id: str) -> str:
        """Format DynamoDB memories as context string."""
        memories = self.recall(user_id)
        if not memories:
            return ""

        context_lines = ["## User History (from DynamoDB):"]
        for mem in memories[-10:]:
            context_lines.append(f"- [{mem['category']}] {mem['key']}: {mem['value']}")
        return "\n".join(context_lines)

    def forget(self, user_id: str, key: str, category: str = "general"):
        """Remove a specific memory."""
        if not self.table:
            return
        try:
            self.table.delete_item(Key={"user_id": user_id, "memory_key": f"{category}#{key}"})
        except Exception as e:
            logger.warning(f"[DynamoDB] Failed to forget: {e}")


class DualMemory:
    """Unified interface combining AgentCore Memory + DynamoDB.
    
    Usage pattern:
    - Agent receives request → retrieve context from BOTH backends
    - Agent processes → store conversation in AgentCore, preferences in DynamoDB
    - Result: Rich semantic context + explicit structured history
    """

    def __init__(self):
        self.agentcore = AgentCoreMemory()
        self.dynamodb = DynamoDBMemory()
        logger.info("[DualMemory] Initialized: AgentCore (semantic) + DynamoDB (structured)")

    def build_context(self, user_id: str, current_prompt: str) -> str:
        """Build complete context from both memory backends."""
        parts = []

        # 1. AgentCore: Semantic context relevant to current query
        agentcore_ctx = self.agentcore.get_context_string(current_prompt)
        if agentcore_ctx:
            parts.append(agentcore_ctx)

        # 2. DynamoDB: User preferences and history
        dynamo_ctx = self.dynamodb.recall_as_context(user_id)
        if dynamo_ctx:
            parts.append(dynamo_ctx)

        return "\n\n".join(parts) if parts else ""

    def store_interaction(self, user_id: str, session_id: str, prompt: str, response: str):
        """Store interaction in both backends after agent responds."""
        # AgentCore: Store full conversation for semantic extraction
        self.agentcore.store_conversation_event(
            session_id=session_id,
            actor="user",
            content=prompt
        )
        self.agentcore.store_conversation_event(
            session_id=session_id,
            actor="agent",
            content=response[:500]  # Truncate long responses
        )

        # DynamoDB: Store interaction summary for history
        self.dynamodb.remember(
            user_id=user_id,
            key=f"session_{session_id[:8]}",
            value=prompt[:100],
            category="interactions"
        )

    def remember_preference(self, user_id: str, key: str, value: str):
        """Explicitly store a user preference in DynamoDB."""
        self.dynamodb.remember(user_id, key, value, category="preferences")

    def recall_preferences(self, user_id: str) -> list:
        """Get all stored preferences for a user."""
        return self.dynamodb.recall(user_id, category="preferences")
