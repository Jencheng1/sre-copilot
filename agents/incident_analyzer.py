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
            
            Please provide your analysis in exactly the following format:

            1. Root Cause Analysis:
            [Main root cause finding]
            Confidence: [Percentage between 0-100]%
            Evidence:
            - [Evidence point 1]
            - [Evidence point 2]
            - [Additional evidence points...]

            2. Impact Analysis:
            [Main impact finding]
            Confidence: [Percentage between 0-100]%
            Evidence:
            - [Evidence point 1]
            - [Evidence point 2]
            - [Additional evidence points...]

            3. Key Findings:
            - [Finding 1]
            - [Finding 2]
            - [Additional findings...]

            4. Recommendations:
            - [Recommendation 1]
            - [Recommendation 2]
            - [Additional recommendations...]

            Please ensure each section follows this exact format with confidence levels as percentages and evidence as bullet points.
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
        
        # Extract key findings and recommendations directly from the analysis result
        key_findings = analysis_result.get("key_findings", [])
        recommendations = analysis_result.get("recommendations", [])
        
        return IncidentAnalysis(
            incident_id=incident.incident_id,
            root_cause=root_cause,
            impact_analysis=impact_analysis,
            metric_insights=[],  # Will be populated by metric analyzer
            log_insights=[],     # Will be populated by log analyzer
            recommendations=recommendations
        ) 