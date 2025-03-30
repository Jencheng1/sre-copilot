from typing import Dict, Any
from models.incident import Incident, IncidentAnalysis, AnalysisInsight
from services.bedrock_service import BedrockService
import json
import logging

class IncidentAnalyzer:
    def __init__(self, bedrock_service: BedrockService):
        self.bedrock_service = bedrock_service
    
    async def analyze(self, incident: Incident) -> IncidentAnalysis:
        """
        Analyze an incident using AWS Bedrock
        """
        logger = logging.getLogger(__name__)
        
        # Prepare incident data for analysis
        incident_data = {
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity,
            "start_time": incident.start_time.isoformat(),
            "end_time": incident.end_time.isoformat() if incident.end_time else None,
            "tags": incident.tags
        }
        
        logger.debug(f"Analyzing incident: {json.dumps(incident_data, indent=2)}")
        
        # Analyze incident details
        analysis_result = await self.bedrock_service.analyze_text(
            json.dumps(incident_data, indent=2),
            """
            Analyze the following incident details and provide a comprehensive analysis:
            
            {text}
            
            Please provide your analysis in exactly the following format, including ALL sections:

            1. Root Cause Analysis:
            [Provide a clear statement of the root cause]
            Confidence: [Number]%
            Evidence:
            - [Specific evidence point]
            - [Additional evidence points...]

            2. Impact Analysis:
            [Provide a clear statement of the impact]
            Confidence: [Number]%
            Evidence:
            - [Specific evidence point]
            - [Additional evidence points...]

            3. Key Findings:
            - [Clear, specific finding]
            - [Additional findings...]

            4. Recommendations:
            - [Clear, actionable recommendation]
            - [Additional recommendations...]

            Ensure each section follows this exact format. Include confidence levels as numbers between 0-100.
            List all evidence points and findings with bullet points.
            """
        )
        
        logger.debug(f"Received analysis result: {json.dumps(analysis_result, indent=2)}")
        
        if "error" in analysis_result:
            logger.error(f"Error in analysis: {analysis_result['error']}")
            logger.debug(f"Raw completion: {analysis_result.get('raw_completion', '')}")
            raise Exception(f"Failed to analyze incident: {analysis_result['error']}")
        
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
        
        logger.debug(f"Root Cause Analysis: {root_cause}")
        logger.debug(f"Impact Analysis: {impact_analysis}")
        
        # Extract key findings and recommendations
        key_findings = analysis_result.get("key_findings", [])
        recommendations = analysis_result.get("recommendations", [])
        
        logger.debug(f"Key Findings: {key_findings}")
        logger.debug(f"Recommendations: {recommendations}")
        
        return IncidentAnalysis(
            incident_id=incident.incident_id,
            root_cause=root_cause,
            impact_analysis=impact_analysis,
            metric_insights=[],  # Will be populated by metric analyzer
            log_insights=[],     # Will be populated by log analyzer
            key_findings=key_findings,  # Added key_findings to the return value
            recommendations=recommendations
        ) 