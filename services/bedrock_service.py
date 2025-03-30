import boto3
import json
from typing import Dict, Any, List
import streamlit as st

class BedrockService:
    def __init__(self):
        if not all(key in st.secrets for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']):
            raise Exception("AWS credentials not found in Streamlit secrets. Please configure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION.")
            
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=st.secrets['AWS_REGION'],
            aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
        )
        
    async def analyze_text(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze text using AWS Bedrock
        """
        try:
            request_body = {
                "prompt": prompt_template.format(text=text),
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.95,
                "stop_sequences": ["\n\n"]
            }
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-v2",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body
        except Exception as e:
            raise Exception(f"Error analyzing text with Bedrock: {str(e)}")
    
    async def analyze_metrics(self, metrics: list) -> Dict[str, Any]:
        """
        Analyze metrics data using AWS Bedrock
        """
        prompt = """
        Analyze the following metrics data and identify patterns, anomalies, and potential issues:
        
        {metrics}
        
        Provide insights in the following format:
        1. Key patterns and trends
        2. Anomalies detected
        3. Potential root causes
        4. Recommendations
        """
        
        metrics_text = json.dumps(metrics, indent=2)
        return await self.analyze_text(metrics_text, prompt)
    
    async def analyze_logs(self, logs: list) -> Dict[str, Any]:
        """
        Analyze log data using AWS Bedrock
        """
        prompt = """
        Analyze the following log data and identify patterns, errors, and potential issues:
        
        {logs}
        
        Provide insights in the following format:
        1. Error patterns and frequencies
        2. Correlated events
        3. Potential root causes
        4. Recommendations
        """
        
        logs_text = "\n".join(logs)
        return await self.analyze_text(logs_text, prompt)
    
    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image data using AWS Bedrock
        """
        try:
            # Convert image to base64
            import base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            request_body = {
                "prompt": "Analyze this image and identify any issues, patterns, or relevant information for incident analysis.",
                "image": image_base64,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body
        except Exception as e:
            raise Exception(f"Error analyzing image with Bedrock: {str(e)}")
    
    async def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on analysis results
        """
        prompt = """
        Based on the following analysis results, generate specific, actionable recommendations:
        
        {analysis}
        
        Provide recommendations in a clear, prioritized list.
        """
        
        analysis_text = json.dumps(analysis_results, indent=2)
        response = await self.analyze_text(analysis_text, prompt)
        return response.get('recommendations', []) 