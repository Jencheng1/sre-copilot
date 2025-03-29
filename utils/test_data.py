from datetime import datetime, timedelta
import random
from typing import List, Dict
from models.incident import Incident, Metric, Log, IncidentAnalysis, AnalysisInsight

def generate_test_incident() -> Incident:
    """
    Generate a sample incident with realistic test data
    """
    # Generate timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=2)
    
    # Generate metrics
    metrics = generate_test_metrics(start_time, end_time)
    
    # Generate logs
    logs = generate_test_logs(start_time, end_time)
    
    # Create incident
    incident = Incident(
        incident_id=f"INC-{random.randint(1000, 9999)}",
        title="High CPU Usage and Service Degradation",
        description="""
        Multiple services experiencing high CPU utilization and increased latency.
        Affected services:
        - User Authentication Service
        - Payment Processing Service
        - Order Management Service
        
        Impact:
        - 30% of users experiencing login issues
        - Payment processing delays up to 5 seconds
        - Order creation failures at 15% rate
        """,
        severity="P1",
        start_time=start_time,
        end_time=end_time,
        metrics=metrics,
        logs=logs,
        tags={
            "environment": "production",
            "region": "us-west-2",
            "team": "platform"
        }
    )
    
    return incident

def generate_test_metrics(start_time: datetime, end_time: datetime) -> List[Metric]:
    """
    Generate realistic test metrics
    """
    metrics = []
    current_time = start_time
    
    # CPU metrics
    while current_time <= end_time:
        metrics.append(Metric(
            name="cpu_usage",
            value=random.uniform(60, 95),
            timestamp=current_time,
            tags={"service": "auth-service"}
        ))
        
        metrics.append(Metric(
            name="cpu_usage",
            value=random.uniform(70, 98),
            timestamp=current_time,
            tags={"service": "payment-service"}
        ))
        
        metrics.append(Metric(
            name="response_time",
            value=random.uniform(100, 5000),
            timestamp=current_time,
            tags={"service": "auth-service"}
        ))
        
        current_time += timedelta(minutes=5)
    
    return metrics

def generate_test_logs(start_time: datetime, end_time: datetime) -> List[Log]:
    """
    Generate realistic test logs
    """
    logs = []
    current_time = start_time
    
    error_messages = [
        "Connection timeout while connecting to database",
        "High memory usage detected",
        "Service health check failed",
        "Rate limit exceeded",
        "Cache miss rate above threshold",
        "Database connection pool exhausted"
    ]
    
    while current_time <= end_time:
        # Generate normal logs
        if random.random() < 0.7:  # 70% normal logs
            logs.append(Log(
                timestamp=current_time,
                level="INFO",
                message=f"Processing request {random.randint(1000, 9999)}",
                source="auth-service"
            ))
        else:  # 30% error logs
            logs.append(Log(
                timestamp=current_time,
                level=random.choice(["ERROR", "WARNING", "CRITICAL"]),
                message=random.choice(error_messages),
                source=random.choice(["auth-service", "payment-service", "order-service"])
            ))
        
        current_time += timedelta(seconds=random.randint(5, 30))
    
    return logs

def generate_test_snapshot() -> IncidentAnalysis:
    """
    Generate a test snapshot of the incident analysis
    """
    return IncidentAnalysis(
        incident_id="INC-1234",
        root_cause=AnalysisInsight(
            description="Database connection pool exhaustion leading to cascading failures",
            confidence=0.85,
            evidence=[
                "Connection pool metrics showing 100% utilization",
                "Multiple 'Database connection pool exhausted' errors in logs",
                "Correlated CPU spikes across services"
            ]
        ),
        impact_analysis=AnalysisInsight(
            description="Service-wide degradation affecting user authentication and payment processing",
            confidence=0.90,
            evidence=[
                "30% increase in error rates",
                "5x increase in response times",
                "15% order creation failure rate"
            ]
        ),
        metric_insights=[
            AnalysisInsight(
                description="CPU usage consistently above 80% for payment service",
                confidence=0.95,
                evidence=["CPU metrics showing sustained high utilization"]
            ),
            AnalysisInsight(
                description="Response time degradation starting at 14:30 UTC",
                confidence=0.88,
                evidence=["Response time metrics showing sudden increase"]
            )
        ],
        log_insights=[
            AnalysisInsight(
                description="Multiple database connection pool exhaustion errors",
                confidence=0.92,
                evidence=["Error logs showing connection pool issues"]
            ),
            AnalysisInsight(
                description="Cascading failures across services",
                confidence=0.85,
                evidence=["Error patterns showing service dependencies"]
            )
        ],
        recommendations=[
            "Increase database connection pool size",
            "Implement circuit breakers for database connections",
            "Add monitoring for connection pool metrics",
            "Review service dependencies and implement better isolation",
            "Consider implementing connection pooling at the application level"
        ]
    ) 