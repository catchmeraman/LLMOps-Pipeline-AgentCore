"""SNS tools for the LLMOps agent."""
import os
import boto3
from strands import tool

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:<YOUR_ACCOUNT_ID>:it-ops-agent-alerts")


@tool
def send_notification(subject: str, message: str) -> dict:
    """Send a notification to the ops team via SNS. Use for alerts and status updates."""
    sns = boto3.client('sns')
    response = sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject[:100],
        Message=message
    )
    return {"message_id": response['MessageId'], "status": "sent", "topic": SNS_TOPIC_ARN}
