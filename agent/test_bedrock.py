"""
Test script to verify AWS Bedrock configuration
"""
import os
import logging
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
import boto3
import json

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)8s] %(name)s - %(message)s"
)

load_dotenv()

def test_bedrock():
    print("="*70)
    print("AWS BEDROCK CONFIGURATION TEST")
    print("="*70)
    
    # Test 1: AWS Credentials
    print("\n1. Testing AWS Credentials...")
    try:
        sts = boto3.client('sts', region_name=os.getenv('AWS_REGION'))
        identity = sts.get_caller_identity()
        print(f"  ✓ Authenticated as: {identity['Arn']}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return
    
    # Test 2: List Available Inference Profiles
    print("\n2. Listing Available Inference Profiles...")
    region = os.getenv('AWS_REGION')
    
    try:
        bedrock = boto3.client('bedrock', region_name=region)
        
        # List inference profiles
        print("\n  Available Inference Profiles:")
        try:
            profiles_response = bedrock.list_inference_profiles()
            for profile in profiles_response.get('inferenceProfileSummaries', []):
                profile_id = profile.get('inferenceProfileId', '')
                if 'nova' in profile_id.lower():
                    print(f"    - {profile_id}")
                    print(f"      ARN: {profile.get('inferenceProfileArn', 'N/A')}")
                    print(f"      Models: {profile.get('models', [])}")
        except Exception as e:
            print(f"  Could not list profiles: {e}")
            print("  Trying common Nova 2 inference profile IDs...")
        
    except Exception as e:
        print(f"  ✗ Failed to connect to Bedrock: {e}")
    
    # Test 3: Try Different Nova 2 Configurations
    print("\n3. Testing Model Invocation with Different Profile IDs...")
    
    # Common Nova 2 inference profile formats
    nova_profiles = [
        "us.amazon.nova-lite-v1:0",
        "us.amazon.nova-micro-v1:0",
        "us.amazon.nova-pro-v1:0",
        "amazon.nova-lite-v1:0",
        "amazon.nova-micro-v1:0",
        os.getenv('BEDROCK_MODEL_ID')  # From .env
    ]
    
    configs = [
        {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9
        }
    ]
    
    for profile_id in nova_profiles:
        if not profile_id:
            continue
            
        print(f"\n  Testing Profile: {profile_id}")
        
        for config in configs:
            try:
                llm = ChatBedrock(
                    model_id=profile_id,
                    region_name=region,
                    model_kwargs=config
                )
                
                response = llm.invoke("Say 'Hello World' briefly")
                print(f"  ✓ SUCCESS with profile: {profile_id}")
                print(f"    Response: {response.content}")
                print(f"    Parameters: {json.dumps(config, indent=6)}")
                print(f"\n  🎉 Use this in your .env file:")
                print(f"      BEDROCK_MODEL_ID={profile_id}")
                return  # Success, exit
                
            except Exception as e:
                error_msg = str(e)
                if "isn't supported" in error_msg or "on-demand throughput" in error_msg:
                    print(f"  ✗ Not available: {profile_id}")
                elif "ValidationException" in error_msg:
                    print(f"  ✗ Validation error: {error_msg[:150]}")
                else:
                    print(f"  ✗ Error: {error_msg[:150]}")
    
    print("\n  ❌ None of the common profiles worked.")
    print("  Please check AWS Bedrock console for available inference profiles:")
    print(f"  https://console.aws.amazon.com/bedrock/home?region={region}#/inference-profiles")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_bedrock()
