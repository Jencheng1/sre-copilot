import logging
import os
import boto3
import json
from typing import Dict, Any, List
import streamlit as st

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
        
    async def analyze_text(self, text: str, prompt_template: str) -> Dict[str, Any]:
        """
        Analyze text using Bedrock's Claude model
        """
        try:
            # Format the prompt with the text parameter and add Claude's required prefixes
            formatted_prompt = f"\n\nHuman: {prompt_template.format(text=text)}\n\nAssistant: I'll analyze this information and provide a structured response."
            
            body = json.dumps({
                "prompt": formatted_prompt,
                "max_tokens_to_sample": 1000,
                "temperature": 0.7,
                "top_p": 0.95,
                "stop_sequences": ["\n\nHuman:"]
            })
            
            logger.debug(f"Sending prompt to Claude: {formatted_prompt}")
            
            response = self.bedrock.invoke_model(
                modelId="anthropic.claude-v2",
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            
            # Extract the completion from Claude's response
            completion = response_body.get('completion', '')
            logger.debug(f"Received completion from Claude: {completion}")
            
            # Parse the completion into structured data
            try:
                # Split the completion into sections
                sections = completion.split('\n\n')
                
                # Initialize the result dictionary
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
                
                # Parse each section
                current_section = None
                for section in sections:
                    if "Root cause analysis" in section:
                        current_section = "root_cause"
                        # Extract confidence and evidence
                        lines = section.split('\n')
                        result["root_cause"] = lines[0].replace("Root cause analysis:", "").strip()
                        for line in lines[1:]:
                            if "confidence" in line.lower():
                                try:
                                    result["root_cause_confidence"] = float(line.split(":")[1].strip().rstrip("%")) / 100
                                except:
                                    pass
                            elif line.strip().startswith("-"):
                                result["root_cause_evidence"].append(line.strip("- "))
                    
                    elif "Impact analysis" in section:
                        current_section = "impact"
                        lines = section.split('\n')
                        result["impact_analysis"] = lines[0].replace("Impact analysis:", "").strip()
                        for line in lines[1:]:
                            if "confidence" in line.lower():
                                try:
                                    result["impact_confidence"] = float(line.split(":")[1].strip().rstrip("%")) / 100
                                except:
                                    pass
                            elif line.strip().startswith("-"):
                                result["impact_evidence"].append(line.strip("- "))
                    
                    elif "Key findings" in section:
                        current_section = "findings"
                        lines = section.split('\n')
                        for line in lines[1:]:
                            if line.strip().startswith("-"):
                                result["key_findings"].append(line.strip("- "))
                    
                    elif "Recommendations" in section:
                        current_section = "recommendations"
                        lines = section.split('\n')
                        for line in lines[1:]:
                            if line.strip().startswith("-") or line.strip()[0].isdigit():
                                result["recommendations"].append(line.strip("- ").strip("1234567890. "))
                
                return result
            except Exception as e:
                logger.error(f"Error parsing Claude's response: {str(e)}")
                # Return the raw completion if parsing fails
                return {"completion": completion}
            
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
        
        metrics_text = json.dumps(metrics, indent=2)
        return await self.analyze_text(metrics_text, prompt)
    
    async def analyze_logs(self, logs: list) -> Dict[str, Any]:
        """
        Analyze log data using AWS Bedrock
        """
        prompt = """
        Analyze the following log data and identify patterns, errors, and potential issues:
        
        {text}
        
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
        
        {text}
        
        Provide recommendations in a clear, prioritized list.
        """
        
        analysis_text = json.dumps(analysis_results, indent=2)
        response = await self.analyze_text(analysis_text, prompt)
        return response.get('recommendations', []) 