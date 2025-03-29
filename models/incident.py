from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class Metric(BaseModel):
    name: str
    value: float
    timestamp: datetime
    tags: Optional[Dict[str, str]] = None

class Log(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: Optional[Dict[str, str]] = None

class Incident(BaseModel):
    incident_id: str
    title: str
    description: str
    severity: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: List[Metric] = []
    logs: List[Log] = []
    tags: Optional[Dict[str, str]] = None

class AnalysisInsight(BaseModel):
    description: str
    confidence: float
    evidence: List[str]

class IncidentAnalysis(BaseModel):
    incident_id: str
    root_cause: AnalysisInsight
    impact_analysis: AnalysisInsight
    metric_insights: List[AnalysisInsight]
    log_insights: List[AnalysisInsight]
    recommendations: List[str]
    timestamp: datetime = datetime.now()

class MetricAnalysis(BaseModel):
    insights: List[AnalysisInsight]
    anomalies: List[Dict[str, Any]]
    trends: List[Dict[str, Any]]

class LogAnalysis(BaseModel):
    insights: List[AnalysisInsight]
    error_patterns: List[Dict[str, Any]]
    correlation_events: List[Dict[str, Any]] 