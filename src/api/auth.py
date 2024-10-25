import os
from typing import Annotated
import boto3
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from api.setting import DEFAULT_API_KEYS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key_param = os.environ.get("bedrock_api_key_param_name")
logger.info(f"API Key Param Name: {api_key_param}")

if api_key_param:
    ssm = boto3.client("ssm")
    logger.info(f"SSM Client Region: {ssm.meta.region_name}")
    try:
        response = ssm.get_parameter(Name=api_key_param, WithDecryption=True)
        logger.info(f"SSM Response: {response}")
        api_key = response["Parameter"]["Value"]
    except Exception as e:
        logger.error(f"Error getting SSM parameter: {str(e)}")
        raise
else:
    api_key = DEFAULT_API_KEYS
    logger.info("Using DEFAULT_API_KEYS")

security = HTTPBearer()


def api_key_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
