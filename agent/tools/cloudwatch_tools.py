"""CloudWatch tools for the LLMOps agent."""
import boto3
from strands import tool
from datetime import datetime, timedelta


@tool
def get_alarms(state: str = "ALARM") -> dict:
    """Get CloudWatch alarms filtered by state. State: ALARM, OK, INSUFFICIENT_DATA, or ALL."""
    cw = boto3.client('cloudwatch')
    if state == "ALL":
        response = cw.describe_alarms()
    else:
        response = cw.describe_alarms(StateValue=state)
    alarms = [
        {"name": a['AlarmName'], "metric": a['MetricName'], "state": a['StateValue'],
         "reason": a['StateReason'][:100]}
        for a in response.get('MetricAlarms', [])
    ]
    return {"alarms": alarms, "count": len(alarms), "filter": state}


@tool
def get_metric_statistics(namespace: str, metric_name: str, dimension_name: str,
                          dimension_value: str, minutes: int = 30) -> dict:
    """Get CloudWatch metric statistics. E.g., namespace=AWS/EC2, metric_name=CPUUtilization, dimension_name=InstanceId, dimension_value=i-xxx."""
    cw = boto3.client('cloudwatch')
    response = cw.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[{'Name': dimension_name, 'Value': dimension_value}],
        StartTime=datetime.utcnow() - timedelta(minutes=minutes),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average', 'Maximum']
    )
    datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
    return {
        "metric": f"{namespace}/{metric_name}",
        "dimension": f"{dimension_name}={dimension_value}",
        "datapoints": [
            {"time": dp['Timestamp'].isoformat(), "avg": round(dp['Average'], 2), "max": round(dp['Maximum'], 2)}
            for dp in datapoints[-6:]
        ]
    }
