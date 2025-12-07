"""
Custom Bedrock client for Amazon Nova 2 models
Ensures only supported parameters are sent to the API
"""
import os
import json
import boto3
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class NovaBedrockClient:
    """Custom client for Amazon Nova 2 that bypasses LangChain parameter issues"""
    
    def __init__(self, model_id: str = None, region_name: str = None, model_kwargs: Dict[str, Any] = None):
        logger.info("Initializing NovaBedrockClient...")
        
        # Use environment variables as defaults
        self.model_id = model_id or os.getenv('BEDROCK_MODEL_ID') or os.getenv('MODEL', 'amazon.nova-pro-v1:0')
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        self.model_kwargs = model_kwargs or {
            "max_new_tokens": int(os.getenv('MAX_TOKENS', '2048')),
            "temperature": float(os.getenv('TEMPERATURE', '0.7'))
        }
        
        # Initialize boto3 bedrock-runtime client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region_name
        )
        
        logger.info(f"Initialized NovaBedrockClient:")
        logger.info(f"  Model: {self.model_id}")
        logger.info(f"  Region: {self.region_name}")
        logger.info(f"  Params: {json.dumps(self.model_kwargs, indent=2)}")
    
    def invoke(self, prompt: str) -> Any:
        """
        Invoke the model with proper Nova 2 API format
        
        Args:
            prompt: Text prompt to send to model
            
        Returns:
            Response object with .content attribute
        """
        logger.info(f"Invoking model with model_id: {self.model_id}")
        logger.debug(f"Prompt length: {len(prompt)}")
        
        # Build the request in Nova 2 format
        # Nova 2 uses the Converse API
        messages = [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ]
        
        # Only include supported parameters
        inference_config = {}
        if "max_new_tokens" in self.model_kwargs:
            inference_config["maxTokens"] = self.model_kwargs["max_new_tokens"]
        if "temperature" in self.model_kwargs:
            inference_config["temperature"] = self.model_kwargs["temperature"]
        if "top_p" in self.model_kwargs:
            inference_config["topP"] = self.model_kwargs["top_p"]
        
        logger.debug(f"Request inference config: {json.dumps(inference_config, indent=2)}")
        
        try:
            # Call Converse API (correct for Nova 2)
            response = self.client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            logger.info("Successfully received response from converse()")
            logger.debug(f"Response keys: {response.keys()}")
            
            # Extract text from response
            content = response['output']['message']['content'][0]['text']
            logger.info(f"Extracted output text (length: {len(content)})")
            
            # Create response object compatible with LangChain
            class Response:
                def __init__(self, text):
                    self.content = text
            
            return Response(content)
            
        except Exception as e:
            logger.error(f"Error invoking model: {str(e)}")
            logger.error(f"Model ID: {self.model_id}")
            logger.error(f"Inference config: {json.dumps(inference_config, indent=2)}")
            raise
