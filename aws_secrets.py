"""
AWS Secrets Manager Integration

Fetches secrets from AWS Secrets Manager and loads them as environment variables.
Falls back to .env file if AWS credentials are not available or if running locally.

Required AWS environment variables:
  AWS_SECRET_NAME          - Name of the secret in AWS Secrets Manager
  AWS_REGION              - AWS region (default: us-east-1)
  
Optional AWS credentials (if not using IAM role):
  AWS_ACCESS_KEY_ID       - AWS access key
  AWS_SECRET_ACCESS_KEY   - AWS secret key
"""

import os
import sys
import json
import logging
from typing import Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    print("⚠️  boto3 not installed. AWS Secrets Manager integration disabled.")
    print("   Install with: pip install boto3")

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_secret_from_aws(secret_name: str, region_name: str = "us-east-1") -> Optional[Dict[str, str]]:
    """
    Fetch secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        region_name: AWS region (default: us-east-1)
        
    Returns:
        Dictionary of secret key-value pairs, or None if failed
    """
    if not BOTO3_AVAILABLE:
        logger.warning("boto3 not available, cannot fetch from AWS Secrets Manager")
        return None
    
    try:
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        logger.info(f"🔐 Fetching secret '{secret_name}' from AWS Secrets Manager (region: {region_name})")
        
        # Fetch the secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        # Parse the secret string (assuming JSON format)
        if 'SecretString' in get_secret_value_response:
            secret_string = get_secret_value_response['SecretString']
            secrets = json.loads(secret_string)
            logger.info(f"✅ Successfully fetched {len(secrets)} secrets from AWS Secrets Manager")
            return secrets
        else:
            logger.error("❌ Secret does not contain SecretString")
            return None
            
    except NoCredentialsError:
        logger.warning("⚠️  AWS credentials not found. Falling back to .env file.")
        return None
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            logger.error(f"❌ Secret '{secret_name}' not found in AWS Secrets Manager")
        elif error_code == 'InvalidRequestException':
            logger.error(f"❌ Invalid request to AWS Secrets Manager: {e}")
        elif error_code == 'InvalidParameterException':
            logger.error(f"❌ Invalid parameter in AWS Secrets Manager request: {e}")
        elif error_code == 'DecryptionFailure':
            logger.error(f"❌ Cannot decrypt secret: {e}")
        elif error_code == 'InternalServiceError':
            logger.error(f"❌ AWS Secrets Manager internal error: {e}")
        else:
            logger.error(f"❌ Error fetching secret from AWS: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse secret as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching secret from AWS: {e}")
        return None


def load_secrets_from_aws(secret_name: Optional[str] = None, region_name: Optional[str] = None) -> bool:
    """
    Load secrets from AWS Secrets Manager and set them as environment variables.
    Falls back to .env file if AWS is not configured.
    
    Args:
        secret_name: Name of the secret (defaults to AWS_SECRET_NAME env var)
        region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
        
    Returns:
        True if secrets were loaded from AWS, False if fell back to .env
    """
    # First, load .env file to get AWS configuration (if any)
    load_dotenv()
    
    # Get AWS configuration
    secret_name = secret_name or os.getenv("AWS_SECRET_NAME")
    region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
    
    # Check if AWS Secrets Manager should be used
    use_aws = os.getenv("USE_AWS_SECRETS", "false").lower() in ("true", "1", "yes")
    
    if not use_aws:
        logger.info("ℹ️  AWS Secrets Manager disabled (USE_AWS_SECRETS not set to true)")
        logger.info("📄 Using .env file for configuration")
        return False
    
    if not secret_name:
        logger.warning("⚠️  AWS_SECRET_NAME not set. Falling back to .env file.")
        logger.info("📄 Using .env file for configuration")
        return False
    
    # Fetch secrets from AWS
    secrets = get_secret_from_aws(secret_name, region_name)
    
    if secrets:
        # Set secrets as environment variables
        for key, value in secrets.items():
            os.environ[key] = str(value)
            logger.debug(f"  ✓ Set environment variable: {key}")
        
        logger.info(f"✅ Loaded {len(secrets)} secrets from AWS Secrets Manager")
        return True
    else:
        logger.warning("⚠️  Failed to fetch secrets from AWS. Using .env file.")
        logger.info("📄 Using .env file for configuration")
        return False


def initialize_environment() -> None:
    """
    Initialize environment variables from AWS Secrets Manager or .env file.
    This should be called at application startup.
    """
    logger.info("🔧 Initializing environment configuration...")
    
    # Try to load from AWS Secrets Manager
    loaded_from_aws = load_secrets_from_aws()
    
    if not loaded_from_aws:
        # Ensure .env is loaded (it was already loaded in load_secrets_from_aws)
        logger.info("📄 Environment loaded from .env file")
    
    # Validate required environment variables
    required_vars = [
        "OPENROUTER_API_KEY",
        "ASTRA_DB_API_ENDPOINT",
        "ASTRA_DB_APPLICATION_TOKEN",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("   Please set them in .env file or AWS Secrets Manager")
        sys.exit(1)
    
    logger.info("✅ Environment initialization complete")


if __name__ == "__main__":
    # Test the AWS Secrets Manager integration
    print("Testing AWS Secrets Manager integration...\n")
    initialize_environment()
    
    # Display loaded configuration (without sensitive values)
    print("\n📋 Configuration Summary:")
    print(f"  USE_AWS_SECRETS: {os.getenv('USE_AWS_SECRETS', 'false')}")
    print(f"  AWS_SECRET_NAME: {os.getenv('AWS_SECRET_NAME', 'not set')}")
    print(f"  AWS_REGION: {os.getenv('AWS_REGION', 'us-east-1')}")
    print(f"  OPENROUTER_API_KEY: {'✓ set' if os.getenv('OPENROUTER_API_KEY') else '✗ not set'}")
    print(f"  ASTRA_DB_API_ENDPOINT: {'✓ set' if os.getenv('ASTRA_DB_API_ENDPOINT') else '✗ not set'}")
    print(f"  ASTRA_DB_APPLICATION_TOKEN: {'✓ set' if os.getenv('ASTRA_DB_APPLICATION_TOKEN') else '✗ not set'}")
