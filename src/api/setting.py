import os

DEFAULT_API_KEYS = "bedrock"

API_ROUTE_PREFIX = "/api/v1"

TITLE = "Amazon Bedrock Proxy APIs"
SUMMARY = "OpenAI-Compatible RESTful APIs for Amazon Bedrock"
VERSION = "0.2.0"
DESCRIPTION = """
Use OpenAI-Compatible RESTful APIs for Amazon Bedrock models.
"""

DEBUG = os.environ.get("DEBUG", "false").lower() != "false"
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
DEFAULT_MODEL = os.environ.get(
    "DEFAULT_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0"
)
FALLBACK_MODEL = os.environ.get(
    "FALLBACK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"
)
DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "DEFAULT_EMBEDDING_MODEL", "cohere.embed-english-v3"
)

OPTILLM_ENABLED = os.environ.get("ENABLE_OPTILLM", "false").lower() == "true"
OPTILLM_APPROACH = os.environ.get("OPTILLM_APPROACH", "auto")
OPTILLM_BEST_OF_N = int(os.environ.get("OPTILLM_BEST_OF_N", "3"))
OPTILLM_MCTS_DEPTH = int(os.environ.get("OPTILLM_MCTS_DEPTH", "1"))
OPTILLM_MCTS_SIMULATIONS = int(os.environ.get("OPTILLM_MCTS_SIMULATIONS", "2"))
OPTILLM_RETURN_FULL = os.environ.get("OPTILLM_RETURN_FULL", "false").lower() == "true"
