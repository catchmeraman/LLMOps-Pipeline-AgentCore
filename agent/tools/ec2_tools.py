"""EC2 tools for the LLMOps agent."""
import boto3
from strands import tool


@tool
def describe_instances(status_filter: str = "all") -> dict:
    """List EC2 instances. Filter: running, stopped, or all."""
    ec2 = boto3.client('ec2')
    filters = [] if status_filter == "all" else [{"Name": "instance-state-name", "Values": [status_filter]}]
    response = ec2.describe_instances(Filters=filters)
    instances = []
    for res in response['Reservations']:
        for inst in res['Instances']:
            name = next((t['Value'] for t in inst.get('Tags', []) if t['Key'] == 'Name'), 'unnamed')
            instances.append({
                "id": inst['InstanceId'], "name": name,
                "type": inst['InstanceType'], "state": inst['State']['Name'],
                "az": inst['Placement']['AvailabilityZone']
            })
    return {"instances": instances, "count": len(instances)}


@tool
def manage_instance(instance_id: str, action: str) -> dict:
    """Start, stop, or reboot an EC2 instance. Action: start, stop, reboot."""
    ec2 = boto3.client('ec2')
    if action == "start":
        ec2.start_instances(InstanceIds=[instance_id])
    elif action == "stop":
        ec2.stop_instances(InstanceIds=[instance_id])
    elif action == "reboot":
        ec2.reboot_instances(InstanceIds=[instance_id])
    else:
        return {"error": f"Unknown action: {action}. Use start, stop, or reboot."}
    return {"instance_id": instance_id, "action": action, "status": "initiated"}
