from typing import Dict, Any
from datetime import datetime
from models.incident import Incident

def validate_incident_data(incident: Incident) -> None:
    """
    Validate incident data before processing
    """
    # Validate required fields
    if not incident.incident_id:
        raise ValueError("Incident ID is required")
    if not incident.title:
        raise ValueError("Incident title is required")
    if not incident.description:
        raise ValueError("Incident description is required")
    if not incident.severity:
        raise ValueError("Incident severity is required")
    if not incident.start_time:
        raise ValueError("Incident start time is required")
    
    # Validate severity levels
    valid_severities = ["P0", "P1", "P2", "P3", "P4"]
    if incident.severity not in valid_severities:
        raise ValueError(f"Invalid severity level. Must be one of: {', '.join(valid_severities)}")
    
    # Validate timestamps
    if incident.end_time and incident.end_time < incident.start_time:
        raise ValueError("End time cannot be before start time")
    
    # Validate metrics
    for metric in incident.metrics:
        if not metric.name:
            raise ValueError("Metric name is required")
        if not isinstance(metric.value, (int, float)):
            raise ValueError("Metric value must be numeric")
        if not metric.timestamp:
            raise ValueError("Metric timestamp is required")
    
    # Validate logs
    for log in incident.logs:
        if not log.timestamp:
            raise ValueError("Log timestamp is required")
        if not log.level:
            raise ValueError("Log level is required")
        if not log.message:
            raise ValueError("Log message is required")
        if not log.source:
            raise ValueError("Log source is required")

def validate_metric_data(metric: Dict[str, Any]) -> None:
    """
    Validate metric data before processing
    """
    required_fields = ["name", "value", "timestamp"]
    for field in required_fields:
        if field not in metric:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(metric["value"], (int, float)):
        raise ValueError("Metric value must be numeric")
    
    if not isinstance(metric["timestamp"], datetime):
        raise ValueError("Metric timestamp must be a datetime object")

def validate_log_data(log: Dict[str, Any]) -> None:
    """
    Validate log data before processing
    """
    required_fields = ["timestamp", "level", "message", "source"]
    for field in required_fields:
        if field not in log:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(log["timestamp"], datetime):
        raise ValueError("Log timestamp must be a datetime object")
    
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log["level"] not in valid_levels:
        raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}") 