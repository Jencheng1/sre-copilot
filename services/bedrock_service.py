import logging
import os
import boto3
import json
from typing import Dict, Any, List
import streamlit as st
import time
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        logger.debug("Initializing BedrockService...")
        logger.debug(f"AWS_REGION from env: {os.getenv('AWS_REGION')}")
        logger.debug(f"AWS_REGION in st.secrets: {st.secrets.get('AWS_REGION')}")
        
        # Check for required AWS configuration in Streamlit secrets
        required_keys = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
        missing_keys = [key for key in required_keys if key not in st.secrets]
        
        if missing_keys:
            error_msg = f"Missing required AWS configuration keys: {', '.join(missing_keys)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        logger.debug("Creating boto3 client with region from st.secrets...")
        try:
            self.bedrock = boto3.client(
                'bedrock-runtime',
                region_name=st.secrets['AWS_REGION'],
                aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY']
            )
            logger.debug("Successfully created boto3 client")
        except Exception as e:
            logger.error(f"Failed to create boto3 client: {str(e)}")
            raise
        
    async def _invoke_with_retry(self, model_id: str, body: str, max_retries: int = 5) -> Dict:
        """
        Invoke Bedrock model with exponential backoff retry logic
        """
        base_delay = 1  # Start with 1 second delay
        for attempt in range(max_retries):
            try:
                response = self.bedrock.invoke_model(
                    modelId=model_id,
                    body=body
                )
                return json.loads(response.get('body').read())
            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    if attempt == max_retries - 1:
                        raise Exception(f"Maximum retries ({max_retries}) reached for throttling. Please try again later.")
                    
                    delay = (base_delay * (2 ** attempt)) + (time.random() * 0.1)  # Add small random jitter
                    logger.warning(f"Request throttled. Retrying in {delay:.2f} seconds... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                raise
            except Exception as e:
                raise Exception(f"Error invoking Bedrock model: {str(e)}")
        
    async def analyze_text(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze text using Bedrock's Claude model
        """
        try:
            # Format the prompt with the text parameter and add Claude's required prefixes
            formatted_prompt = f"\n\nHuman: {prompt_template.format(text=text)}\n\nAssistant: I'll analyze this information and provide a structured response following the exact format specified."
            
            body = json.dumps({
                "prompt": formatted_prompt,
                "max_tokens_to_sample": 2000,
                "temperature": 0.5,  # Reduced for more consistent formatting
                "top_p": 0.99,
                "stop_sequences": ["\n\nHuman:"]
            })
            
            logger.debug(f"Sending prompt to Claude: {formatted_prompt}")
            
            response_body = await self._invoke_with_retry("anthropic.claude-v2", body)
            completion = response_body.get('completion', '')
            logger.debug(f"Raw completion from Claude: {completion}")
            
            # Parse the completion into structured data
            try:
                # Initialize the result dictionary with default values
                result = {
                    "root_cause": "",
                    "root_cause_confidence": 0.0,
                    "root_cause_evidence": [],
                    "impact_analysis": "",
                    "impact_confidence": 0.0,
                    "impact_evidence": [],
                    "key_findings": [],
                    "recommendations": []
                }
                
                # Split into major sections
                sections = completion.split('\n\n')
                current_section = None
                
                for section in sections:
                    logger.debug(f"Processing section: {section}")
                    lines = [line.strip() for line in section.split('\n') if line.strip()]
                    
                    if not lines:
                        continue
                        
                    first_line = lines[0]
                    
                    # Identify section
                    if "1. Root Cause Analysis:" in first_line:
                        current_section = "root_cause"
                        if len(lines) > 1:
                            result["root_cause"] = lines[1]
                            logger.debug(f"Found root cause: {lines[1]}")
                            
                    elif "2. Impact Analysis:" in first_line:
                        current_section = "impact"
                        if len(lines) > 1:
                            result["impact_analysis"] = lines[1]
                            logger.debug(f"Found impact analysis: {lines[1]}")
                            
                    elif "3. Key Findings:" in first_line:
                        current_section = "findings"
                        findings = [line.strip("- ").strip() for line in lines[1:] if line.startswith("-")]
                        result["key_findings"] = findings
                        logger.debug(f"Found key findings: {findings}")
                            
                    elif "4. Recommendations:" in first_line:
                        current_section = "recommendations"
                        recommendations = [line.strip("- ").strip() for line in lines[1:] if line.startswith("-")]
                        result["recommendations"] = recommendations
                        logger.debug(f"Found recommendations: {recommendations}")
                    
                    # Process confidence levels
                    elif "Confidence:" in first_line:
                        confidence_str = first_line.split("Confidence:")[1].strip().rstrip("%")
                        try:
                            confidence = float(confidence_str) / 100.0
                            if current_section == "root_cause":
                                result["root_cause_confidence"] = confidence
                                logger.debug(f"Found root cause confidence: {confidence}")
                            elif current_section == "impact":
                                result["impact_confidence"] = confidence
                                logger.debug(f"Found impact confidence: {confidence}")
                        except ValueError as e:
                            logger.error(f"Failed to parse confidence value '{confidence_str}': {str(e)}")
                    
                    # Process evidence points
                    elif "Evidence:" in first_line:
                        continue  # Skip the "Evidence:" header line
                    
                    elif current_section in ["root_cause", "impact"] and first_line.startswith("-"):
                        evidence = [line.strip("- ").strip() for line in lines if line.startswith("-")]
                        if current_section == "root_cause":
                            result["root_cause_evidence"] = evidence
                            logger.debug(f"Found root cause evidence: {evidence}")
                        else:
                            result["impact_evidence"] = evidence
                            logger.debug(f"Found impact evidence: {evidence}")
                
                logger.debug(f"Final parsed result: {json.dumps(result, indent=2)}")
                return result
                
            except Exception as e:
                logger.error(f"Error parsing Claude's response: {str(e)}")
                logger.error(f"Raw completion: {completion}")
                return {
                    "error": f"Failed to parse response: {str(e)}",
                    "raw_completion": completion
                }
            
        except Exception as e:
            logger.error(f"Error analyzing text with Bedrock: {str(e)}")
            raise Exception(f"Error analyzing text with Bedrock: {str(e)}")
    
    async def analyze_metrics(self, metrics: list) -> Dict[str, Any]:
        """
        Analyze metrics data using AWS Bedrock
        """
        prompt = """
        Analyze the following metrics data and identify patterns, anomalies, and potential issues:
        
        {text}
        
        Provide insights in the following format:
        1. Key patterns and trends
        2. Anomalies detected
        3. Potential root causes
        4. Recommendations
        """
        
        # Convert metrics to serializable format
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": metric.tags or {}
            })
        
        metrics_text = json.dumps(metrics_data, indent=2)
        return await self.analyze_text(metrics_text, prompt)
    
    async def analyze_logs(self, logs: list) -> Dict[str, Any]:
        """
        Analyze log data using AWS Bedrock
        """
        prompt = """
        Analyze the following log entries and identify patterns, errors, and potential issues:
        
        {text}
        
        Provide insights in the following format:
        1. Error patterns and frequencies
        2. Correlated events
        3. Potential root causes
        4. Recommendations for addressing the identified issues
        """
        
        # Convert logs to serializable format
        logs_data = []
        for log in logs:
            log_entry = {
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "source": log.source
            }
            if log.metadata:
                log_entry["metadata"] = log.metadata
            logs_data.append(log_entry)
        
        # Format logs for analysis
        formatted_logs = []
        for log_data in logs_data:
            metadata_str = ""
            if "metadata" in log_data:
                metadata_str = f" {json.dumps(log_data['metadata'])}"
            formatted_logs.append(
                f"{log_data['timestamp']} [{log_data['level']}] {log_data['source']}: {log_data['message']}{metadata_str}"
            )
        
        logs_text = json.dumps({
            "log_entries": logs_data,
            "formatted_logs": formatted_logs
        }, indent=2)
        
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
        
        {text}
        
        Provide recommendations in a clear, prioritized list.
        """
        
        # If analysis_results is a Pydantic model, convert it to dict
        if hasattr(analysis_results, 'model_dump'):
            analysis_text = json.dumps(analysis_results.model_dump(), indent=2)
        else:
            analysis_text = json.dumps(analysis_results, indent=2)
            
        response = await self.analyze_text(analysis_text, prompt)
        return response.get('recommendations', []) 