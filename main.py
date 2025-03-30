from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging
from services.bedrock_service import BedrockService
from agents.incident_analyzer import IncidentAnalyzer
from agents.metric_analyzer import MetricAnalyzer
from agents.log_analyzer import LogAnalyzer
from models.incident import Incident, IncidentAnalysis
from utils.validators import validate_incident_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="SRE Copilot - Incident RCA System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services lazily
_bedrock_service = None
_incident_analyzer = None
_metric_analyzer = None
_log_analyzer = None

def get_services():
    global _bedrock_service, _incident_analyzer, _metric_analyzer, _log_analyzer
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
        _incident_analyzer = IncidentAnalyzer(_bedrock_service)
        _metric_analyzer = MetricAnalyzer(_bedrock_service)
        _log_analyzer = LogAnalyzer(_bedrock_service)
    return _bedrock_service, _incident_analyzer, _metric_analyzer, _log_analyzer

async def analyze_incident(incident: Incident, bedrock_service: BedrockService = None):
    """
    Analyze an incident using multiple agents for comprehensive RCA
    """
    logger.debug("Starting incident analysis...")
    
    # Validate incident data
    logger.debug("Validating incident data...")
    validate_incident_data(incident)
    
    # Initialize services if not provided
    if bedrock_service is None:
        logger.debug("Initializing BedrockService...")
        bedrock_service = BedrockService()
    
    logger.debug("Initializing analyzers...")
    incident_analyzer = IncidentAnalyzer(bedrock_service)
    metric_analyzer = MetricAnalyzer(bedrock_service)
    log_analyzer = LogAnalyzer(bedrock_service)
    
    try:
        logger.debug("Running incident analysis...")
        # Run parallel analysis using different agents
        incident_analysis = await incident_analyzer.analyze(incident)
        logger.debug("Incident analysis completed")
        
        logger.debug("Running metrics analysis...")
        metric_analysis = await metric_analyzer.analyze(incident.metrics)
        logger.debug("Metrics analysis completed")
        
        logger.debug("Running logs analysis...")
        log_analysis = await log_analyzer.analyze(incident.logs)
        logger.debug("Logs analysis completed")
        
        logger.debug("Combining analyses...")
        # Combine analyses
        combined_analysis = IncidentAnalysis(
            incident_id=incident.incident_id,
            root_cause=incident_analysis.root_cause,
            impact_analysis=incident_analysis.impact_analysis,
            metric_insights=metric_analysis.insights,
            log_insights=log_analysis.insights,
            recommendations=incident_analysis.recommendations
        )
        
        logger.debug("Analysis completed successfully")
        return combined_analysis
    except Exception as e:
        logger.error(f"Analysis failed with error: {str(e)}")
        # Re-raise the exception with the original error message
        raise Exception(str(e))

@app.post("/analyze/metrics")
async def analyze_metrics_endpoint(metrics: List[dict]):
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
async def analyze_logs_endpoint(logs: List[str]):
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
async def analyze_image_endpoint(image: UploadFile = File(...)):
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