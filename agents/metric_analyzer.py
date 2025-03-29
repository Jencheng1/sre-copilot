from typing import List, Dict, Any
from models.incident import MetricAnalysis, AnalysisInsight
from services.bedrock_service import BedrockService
import pandas as pd
import numpy as np

class MetricAnalyzer:
    def __init__(self, bedrock_service: BedrockService):
        self.bedrock_service = bedrock_service
    
    async def analyze(self, metrics: List[Dict[str, Any]]) -> MetricAnalysis:
        """
        Analyze metrics data using statistical analysis and AWS Bedrock
        """
        if not metrics:
            return MetricAnalysis(
                insights=[],
                anomalies=[],
                trends=[]
            )
        
        # Convert metrics to DataFrame for analysis
        df = pd.DataFrame(metrics)
        
        # Perform statistical analysis
        anomalies = self._detect_anomalies(df)
        trends = self._analyze_trends(df)
        
        # Prepare data for Bedrock analysis
        analysis_data = {
            "metrics": metrics,
            "anomalies": anomalies,
            "trends": trends
        }
        
        # Get insights from Bedrock
        bedrock_analysis = await self.bedrock_service.analyze_metrics(metrics)
        
        # Extract insights
        insights = [
            AnalysisInsight(
                description=insight.get("description", ""),
                confidence=insight.get("confidence", 0.0),
                evidence=insight.get("evidence", [])
            )
            for insight in bedrock_analysis.get("insights", [])
        ]
        
        return MetricAnalysis(
            insights=insights,
            anomalies=anomalies,
            trends=trends
        )
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metric data using statistical methods
        """
        anomalies = []
        
        for column in df.select_dtypes(include=[np.number]).columns:
            # Calculate mean and standard deviation
            mean = df[column].mean()
            std = df[column].std()
            
            # Detect anomalies (values outside 3 standard deviations)
            anomaly_mask = abs(df[column] - mean) > 3 * std
            anomaly_indices = df[anomaly_mask].index
            
            if len(anomaly_indices) > 0:
                anomalies.append({
                    "metric": column,
                    "anomaly_indices": anomaly_indices.tolist(),
                    "values": df.loc[anomaly_indices, column].tolist(),
                    "mean": mean,
                    "std": std
                })
        
        return anomalies
    
    def _analyze_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Analyze trends in metric data
        """
        trends = []
        
        for column in df.select_dtypes(include=[np.number]).columns:
            # Calculate trend using linear regression
            x = np.arange(len(df))
            slope, intercept = np.polyfit(x, df[column], 1)
            
            # Determine trend direction
            trend_direction = "increasing" if slope > 0 else "decreasing"
            
            trends.append({
                "metric": column,
                "direction": trend_direction,
                "slope": slope,
                "intercept": intercept,
                "strength": abs(slope)  # Higher absolute value indicates stronger trend
            })
        
        return trends 