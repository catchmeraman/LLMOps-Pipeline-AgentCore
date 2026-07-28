"""Deploy script: Update AgentCore Runtime to new container image (bumps version)."""
import boto3
import sys
import time

REGION = "us-east-1"

def deploy(runtime_id: str, container_uri: str):
    client = boto3.client('bedrock-agentcore-control', region_name=REGION)
    
    # Get current runtime config
    current = client.get_agent_runtime(agentRuntimeId=runtime_id)
    current_version = current.get('agentRuntimeVersion', '?')
    print(f"Current runtime: {runtime_id} v{current_version} ({current['status']})")
    
    # Update runtime with new container URI
    response = client.update_agent_runtime(
        agentRuntimeId=runtime_id,
        agentRuntimeArtifact={
            'containerConfiguration': {
                'containerUri': container_uri
            }
        },
        description=f"LLMOps Agent v{int(current_version)+1} - Dual Memory + Guardrails + CI/CD auto-deploy",
        roleArn=current['roleArn'],
        networkConfiguration=current['networkConfiguration'],
        environmentVariables=current.get('environmentVariables', {})
    )
    
    print(f"Update triggered: {response.get('status', 'UPDATING')}")
    
    # Wait for READY
    for i in range(30):
        time.sleep(10)
        status = client.get_agent_runtime(agentRuntimeId=runtime_id)
        state = status.get('status')
        version = status.get('agentRuntimeVersion', '?')
        print(f"  [{i*10}s] Status: {state} | Version: v{version}")
        if state == 'READY':
            print(f"\n✅ Runtime deployed: v{version} READY")
            return
        elif state == 'FAILED':
            print(f"\n❌ Runtime deploy FAILED")
            sys.exit(1)
    
    print("\n⚠️  Timeout waiting for READY (may still be updating)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python deploy_runtime.py <runtime_id> <container_uri>")
        sys.exit(1)
    
    deploy(sys.argv[1], sys.argv[2])
