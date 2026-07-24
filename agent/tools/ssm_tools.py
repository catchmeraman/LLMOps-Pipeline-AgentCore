"""SSM tools for the LLMOps agent."""
import boto3
import time
from strands import tool


@tool
def run_command(instance_id: str, command: str) -> dict:
    """Run a shell command on an EC2 instance via SSM. Returns output."""
    ssm = boto3.client('ssm')
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={"commands": [command]},
        TimeoutSeconds=30
    )
    command_id = response['Command']['CommandId']
    time.sleep(4)
    try:
        output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
        return {
            "status": output['Status'],
            "output": output['StandardOutputContent'][:500],
            "error": output['StandardErrorContent'][:200] if output['StandardErrorContent'] else None
        }
    except Exception as e:
        return {"status": "pending", "message": f"Command sent (id: {command_id}). Check back shortly.", "error": str(e)}
