from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from services.bedrock_service import BedrockService
from agents.incident_analyzer import IncidentAnalyzer
from agents.metric_analyzer import MetricAnalyzer
from agents.log_analyzer import LogAnalyzer
from models.incident import Incident, IncidentAnalysis
from utils.validators import validate_incident_data

app = FastAPI(title="SRE Copilot - Incident RCA System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze/incident", response_model=IncidentAnalysis)
async def analyze_incident(incident: Incident):
    """
    Analyze an incident using multiple agents for comprehensive RCA
    """
    try:
        # Validate incident data
        validate_incident_data(incident)
        
        # Initialize services
        bedrock_service = BedrockService()
        incident_analyzer = IncidentAnalyzer(bedrock_service)
        metric_analyzer = MetricAnalyzer(bedrock_service)
        log_analyzer = LogAnalyzer(bedrock_service)
        
        # Run parallel analysis using different agents
        incident_analysis = await incident_analyzer.analyze(incident)
        metric_analysis = await metric_analyzer.analyze(incident.metrics)
        log_analysis = await log_analyzer.analyze(incident.logs)
        
        # Combine analyses
        combined_analysis = IncidentAnalysis(
            incident_id=incident.incident_id,
            root_cause=incident_analysis.root_cause,
            impact_analysis=incident_analysis.impact_analysis,
            metric_insights=metric_analysis.insights,
            log_insights=log_analysis.insights,
            recommendations=incident_analysis.recommendations
        )
        
        return combined_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/metrics")
async def analyze_metrics(metrics: List[dict]):
    """
    Analyze metrics data specifically
    """
    try:
        bedrock_service = BedrockService()
        metric_analyzer = MetricAnalyzer(bedrock_service)
        analysis = await metric_analyzer.analyze(metrics)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/logs")
async def analyze_logs(logs: List[str]):
    """
    Analyze log data specifically
    """
    try:
        bedrock_service = BedrockService()
        log_analyzer = LogAnalyzer(bedrock_service)
        analysis = await log_analyzer.analyze(logs)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/image")
async def analyze_image(image: UploadFile = File(...)):
    """
    Analyze incident-related images (e.g., dashboards, error screenshots)
    """
    try:
        bedrock_service = BedrockService()
        analysis = await bedrock_service.analyze_image(image)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 