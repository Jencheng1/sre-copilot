from typing import List, Dict, Any
from models.incident import LogAnalysis, AnalysisInsight, Log
from services.bedrock_service import BedrockService
import re
from collections import Counter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LogAnalyzer:
    def __init__(self, bedrock_service: BedrockService):
        self.bedrock_service = bedrock_service
    
    async def analyze(self, logs: List[Log]) -> LogAnalysis:
        """
        Analyze log data using pattern matching and AWS Bedrock
        """
        if not logs:
            return LogAnalysis(
                insights=[],
                error_patterns=[],
                correlation_events=[]
            )
        
        # Convert logs to strings for pattern analysis
        log_strings = [
            f"{log.timestamp.isoformat()} [{log.level}] {log.source}: {log.message}"
            for log in logs
        ]
        
        # Perform pattern analysis
        error_patterns = self._analyze_error_patterns(log_strings)
        correlation_events = self._analyze_correlations(log_strings)
        
        # Get insights from Bedrock
        bedrock_analysis = await self.bedrock_service.analyze_logs(logs)
        
        # Extract insights
        insights = [
            AnalysisInsight(
                description=insight.get("description", ""),
                confidence=insight.get("confidence", 0.0),
                evidence=insight.get("evidence", [])
            )
            for insight in bedrock_analysis.get("insights", [])
        ]
        
        return LogAnalysis(
            insights=insights,
            error_patterns=error_patterns,
            correlation_events=correlation_events
        )
    
    def _analyze_error_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze error patterns in logs
        """
        error_patterns = []
        
        # Common error patterns
        error_levels = ["ERROR", "FATAL", "CRITICAL", "FAILED"]
        error_pattern = re.compile(rf"({'|'.join(error_levels)}).*?:(.*?)(?:\n|$)")
        
        # Extract error messages
        error_messages = []
        for log in logs:
            matches = error_pattern.finditer(log)
            for match in matches:
                error_messages.append({
                    "level": match.group(1),
                    "message": match.group(2).strip()
                })
        
        # Analyze error frequencies
        if error_messages:
            error_counts = Counter(msg["message"] for msg in error_messages)
            
            for message, count in error_counts.most_common():
                error_patterns.append({
                    "message": message,
                    "frequency": count,
                    "level": next(msg["level"] for msg in error_messages if msg["message"] == message)
                })
        
        return error_patterns
    
    def _analyze_correlations(self, logs: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze correlated events in logs
        """
        correlations = []
        
        # Extract timestamps and events
        timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        events = []
        
        for log in logs:
            timestamp_match = timestamp_pattern.search(log)
            if timestamp_match:
                timestamp_str = timestamp_match.group(0)
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    events.append({
                        "timestamp": timestamp,
                        "content": log
                    })
                except ValueError as e:
                    logger.warning(f"Failed to parse timestamp {timestamp_str}: {e}")
                    continue
        
        # Sort events by timestamp
        events.sort(key=lambda x: x["timestamp"])
        
        # Look for correlated events within a time window (e.g., 5 minutes)
        time_window = 300  # 5 minutes in seconds
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                time_diff = (events[j]["timestamp"] - events[i]["timestamp"]).total_seconds()
                if time_diff <= time_window:
                    # Check for related content
                    if self._are_events_related(events[i]["content"], events[j]["content"]):
                        correlations.append({
                            "event1": events[i]["content"],
                            "event2": events[j]["content"],
                            "time_diff": time_diff,
                            "timestamp1": events[i]["timestamp"].isoformat(),
                            "timestamp2": events[j]["timestamp"].isoformat()
                        })
        
        return correlations
    
    def _are_events_related(self, event1: str, event2: str) -> bool:
        """
        Check if two events are related based on content similarity
        """
        # Extract key terms from events
        terms1 = set(re.findall(r"\b\w+\b", event1.lower()))
        terms2 = set(re.findall(r"\b\w+\b", event2.lower()))
        
        # Calculate similarity (Jaccard similarity)
        intersection = len(terms1.intersection(terms2))
        union = len(terms1.union(terms2))
        
        if union == 0:
            return False
        
        similarity = intersection / union
        return similarity > 0.3  # Threshold for considering events related 