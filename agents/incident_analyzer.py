from typing import Dict, Any
from models.incident import Incident, IncidentAnalysis, AnalysisInsight
from services.bedrock_service import BedrockService
import json

class IncidentAnalyzer:
    def __init__(self, bedrock_service: BedrockService):
        self.bedrock_service = bedrock_service
    
    async def analyze(self, incident: Incident) -> IncidentAnalysis:
        """
        Analyze an incident using AWS Bedrock
        """
        # Prepare incident data for analysis
        incident_data = {
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "start_time": incident.start_time.isoformat(),
            "end_time": incident.end_time.isoformat() if incident.end_time else None,
            "tags": incident.tags
        }
        
        # Analyze incident details
        analysis_result = await self.bedrock_service.analyze_text(
            json.dumps(incident_data, indent=2),
            """
            Analyze the following incident details and provide a comprehensive analysis:
            
            {text}
            
            Provide analysis in the following format:
            1. Root cause analysis with confidence level and evidence
            2. Impact analysis with confidence level and evidence
            3. Key findings and patterns
            4. Recommendations for prevention and mitigation
            """
        )
        
        # Extract insights from analysis
        root_cause = AnalysisInsight(
            description=analysis_result.get("root_cause", "Unknown"),
            confidence=analysis_result.get("root_cause_confidence", 0.0),
            evidence=analysis_result.get("root_cause_evidence", [])
        )
        
        impact_analysis = AnalysisInsight(
            description=analysis_result.get("impact_analysis", "Unknown"),
            confidence=analysis_result.get("impact_confidence", 0.0),
            evidence=analysis_result.get("impact_evidence", [])
        )
        
        # Generate recommendations
        recommendations = await self.bedrock_service.generate_recommendations(analysis_result)
        
        return IncidentAnalysis(
            incident_id=incident.incident_id,
            root_cause=root_cause,
            impact_analysis=impact_analysis,
            metric_insights=[],  # Will be populated by metric analyzer
            log_insights=[],     # Will be populated by log analyzer
            recommendations=recommendations
        ) 